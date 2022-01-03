#!/usr/bin/env python
import functools
import json
import os
import pickle
import shutil
import time
from pathlib import Path

import fire
import requests

from nlx.conf.settings import (
    NLX_API_KEY,
    NLX_API_URL,
    NLX_LOG_LEVEL,
    NLX_REPORT_DOWNLOAD_DIR,
    NLX_REPORT_HISTORY_STORAGE,
)
from nlx.utils.dict_utils import as_json, get_all
from nlx.utils.misc import basic_logger
from nlx.utils.settings_utils import ALTERNATE_SEPARATOR

logger = basic_logger(__name__, NLX_LOG_LEVEL)


def format_url(url):
    return f"{str(NLX_API_URL).strip('/')}/{url.strip('/')}/"


def wait(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        if response.status_code == requests.codes.too_many:
            logger.debug(f"throttled, waiting...")
            time.sleep(5)
            return wait(func)(*args, **kwargs)
        return response

    return wrapper


session = requests.Session()
session.headers.update({"X-API-Key": NLX_API_KEY})
session.params.update(dict(timeout=10))


class BaseClient:
    """
    Provides wrappers around requests.get and requests.post which automatically patiently
    waits in the case of response throttling.
    """

    _is_authorized = None

    @property
    def is_authorized(self):
        if self._is_authorized is None:
            logger.debug("contacting API to verify authorization...")
            response = self.get("api")
            if response.status_code == requests.codes.forbidden:
                self._is_authorized = False
            elif response.status_code == requests.codes.ok:
                self._is_authorized = True
            else:
                raise ValueError(f"Expected status codes 200 or 403, got {response.status_code}")
        return self._is_authorized

    @staticmethod
    def get(url, *args, **kwargs):
        url = format_url(url)
        logger.debug(f"GET {url}")
        return wait(session.get)(url, *args, **kwargs)

    @staticmethod
    def post(url, *args, **kwargs):
        url = format_url(url)
        logger.debug(f"POST {url}")
        return wait(session.post)(url, *args, **kwargs)


class AsyncReport(BaseClient):
    """
    Helper class to facilitate requesting and retrieving Async Reports from the NLx API
    """

    def __init__(self):
        history = {}
        if NLX_REPORT_HISTORY_STORAGE.exists():
            with open(NLX_REPORT_HISTORY_STORAGE, "rb") as history_rb:
                history = pickle.load(history_rb)
        self._history = {"downloads": {}, "created": {}, **history}

    def _save(self):
        with open(NLX_REPORT_HISTORY_STORAGE, "wb") as history_wb:
            pickle.dump(self._history, history_wb)

    def save(self, response, creation=None, local_file=None):
        payload = response["data"][0]
        creation_uuid, creation_args = creation if creation else [None, None]
        update_body = response != self._history.get(payload["uuid"])
        update_download = local_file and local_file != self._history["downloads"].get(local_file)
        update_created = creation_args and self._history["created"].get(creation_args) != creation_uuid
        if update_body:
            self._history[payload["uuid"]] = payload
        if update_download:
            self._history["downloads"][payload["uuid"]] = local_file
        if update_created:
            self._history["created"][creation_args] = creation_uuid
        if update_body or update_download or update_created:
            self._save()

    @as_json
    def history(self, id=None):
        """
        View the history of downloaded reports
        :return: JSON object describing downloaded reports
        """
        if id:
            return dict(data=[self._history[id]]) if id in self._history else None
        return self._history

    @as_json
    def create(
        self,
        state,
        start,
        end,
        date_column="date_compiled",
        format="csv",
        classifications_naics_code=None,
        classifications_onet_code=None,
        zipcode=None,
        fein=None,
        auto=False,
    ):
        """
        Create a new Async Report Request and optionally wait for it to finish being created.
        :param state: state or territory corresponding to the desired report
        :param start: beginning (inclusive) of the date range
        :param end: end (exclusive) of the date range
        :param date_column: lookup column of the date range, created_date if unspecified;
            options are [created_date, date_compiled, last_updated_date, date_acquired]
        :param format: output format of the report; options are [csv, ndjson]
        :param classifications_naics_code: naics code of the listings
        :param classifications_onet_code: onet code of the listings
        :param zipcode: zipcode of the listings
        :param fein: fein of the listings
        :param auto: whether to automatically wait and download the report when completed
        :return: JSON response from the API
        """
        query = {
            key: value
            for key, value in dict(
                state_or_territory=state,
                start=start,
                end=end,
                date_column=date_column,
                format=format,
                classifications_naics_code=classifications_naics_code,
                classifications_onet_code=classifications_onet_code,
                zipcode=zipcode,
                fein=fein,
            ).items()
            if value
        }
        creation_args = ALTERNATE_SEPARATOR.join(str(value) for value in query.values())
        if creation_args in self._history["created"]:
            uuid = self._history["created"][creation_args]
            response = json.loads(self.history(uuid))
        else:
            response = self.post("api/job_reports", json=query)
            if response.status_code not in [requests.codes.ok, requests.codes.accepted]:
                response_json = response.json()
                logger.error(f"Unexpected {response.status_code}: {json.dumps(response_json, indent=2)}")
                return response_json
            response = response.json()
            self.save(response, creation=[response["data"][0]["uuid"], creation_args])
        if auto:
            return json.loads(self.download(response["data"][0]["uuid"]))
        return response

    @as_json
    def get_report(self, id):
        """
        Get the status of a report request in progress
        :param id: ID of the report request, returned from the JSON response on creation
        :return: JSON response from the API
        """
        url = format_url(f"api/job_reports/{id}/")
        logger.info(f"checking for status of {id} at {url}")
        response = self.get(f"api/job_reports/{id}/")
        if response.status_code != requests.codes.ok:
            logger.error(f"expected status 200, got {response.status_code}")
        return response.json()

    @as_json
    def download(self, *ids):
        """
        Poll the API for the statuses of the indicated report requests in progress or all report requests
        found in history if no `ids` parameter is provided, download them when possible.
        :param ids: iterable report request IDs to poll
        :return: JSON {id: report_location}
        """
        ids = (
            [key for key, value in self._history.items() if value["status"] in {"created", "in_progress"}]
            if not ids
            else list(ids)
        )
        report = {}

        def _wait(*_ids):
            if not _ids:
                return logger.info("done downloading")
            for id in _ids:
                existing_download = self._history["downloads"].get(id, None)
                existing_download = Path(existing_download)
                desired_location = NLX_REPORT_DOWNLOAD_DIR / Path(existing_download).name
                if desired_location:
                    if desired_location.exists() or existing_download.exists():
                        # if the file isn't downloaded in the desired location, we move it there.
                        if existing_download.exists() and desired_location != existing_download:
                            logger.info(f"{existing_download} detected; relocating to {desired_location}")
                            os.makedirs(desired_location.parent, exist_ok=True)
                            shutil.copy(existing_download, desired_location)
                            os.remove(existing_download)
                            self._history["downloads"][id] = str(desired_location)
                            self._save()
                        ids.remove(id)
                        logger.info(f"skipping download for {id}; already downloaded to {desired_location}")
                        continue
                response = json.loads(self.get_report(id))
                self.save(response)
                if response["data"][0]["resource"]["link"]:
                    ids.remove(id)
                    state, start, format, date_column = get_all(
                        response["data"][0]["query"], "state_or_territory", "start", "format", "date_column"
                    )
                    year, month = start[:4], start[5:7]
                    destination = NLX_REPORT_DOWNLOAD_DIR / Path(f"{state}__{date_column}_{year}_{month}.{format}")
                    os.makedirs(NLX_REPORT_DOWNLOAD_DIR, exist_ok=True)
                    try:
                        with open(destination, "wb") as report_wb:
                            logger.info(f"downloading report {destination} ({id})")
                            for chunk in requests.get(response["data"][0]["resource"]["link"]).iter_content():
                                report_wb.write(chunk)
                    except:  # noqa
                        os.remove(destination)
                        logger.error("encountered error while writing file; cleaning up")
                        raise
                    report[id] = str(destination)
                    self.save(response, local_file=destination)
                time.sleep(3)
            return True

        while _wait(*ids):
            continue
        return report


if __name__ == "__main__":
    fire.Fire(AsyncReport)
