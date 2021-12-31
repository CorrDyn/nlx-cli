#!/usr/bin/env python
import json
import os
import sys

import fire
import rich

from nlx.client import AsyncReport
from nlx.conf import settings
from nlx.utils.misc import basic_logger, cast, confirm
from nlx.utils.module_loading import cached_import, import_or_object

logger = basic_logger(__name__, settings.NLX_LOG_LEVEL)


def load_config(run_config):
    # ensure modules in the user's current directory are importable
    sys.path.insert(0, os.getcwd())
    run_config_module = cached_import(run_config)
    # if the run_config_module.RUNNER_CLIENT is a string,
    # we try to import it and use it, otherwise we use it as the ClientClass
    # directly
    ClientClass = import_or_object(run_config_module.RUNNER_CLIENT)
    client = ClientClass()
    ops = import_or_object(run_config_module.RUNNER_OPS)
    handler = import_or_object(run_config_module.RUNNER_OP_ERROR_HANDLER)
    return client, ops, handler


def sliced(container, offset, limit):
    _offset, offset_valid = cast(offset, int)
    if offset and not offset_valid:
        logger.warning(f"Received invalid offset {offset}")
    start = offset if offset_valid else None
    _limit, limit_valid = cast(limit, int)
    if limit and not limit_valid:
        logger.warning(f"Received invalid limit {offset}")
    end = None
    if offset_valid and limit_valid:
        end = _offset + _limit
    elif limit_valid:
        end = _limit
    return container[start:end]


class Runner:
    async_report = AsyncReport

    @staticmethod
    def show_ops(run_config, offset=None, limit=None):
        _, ops, __ = load_config(run_config)
        ops = sliced(ops, offset, limit)
        for op in ops:
            print(json.dumps(op))

    @staticmethod
    def run(run_config, yes=False, offset=None, limit=None):
        """
        Execute a python module as a series of API Calls
        :param run_config: python import module path containing the run config
        :param yes: auto-confirm any prompts
        :return:
        """
        client, ops, handler = load_config(str(run_config))
        ops = sliced(ops, offset, limit)
        if not client.is_authorized:
            rich.print("[red]Client could not be authenticated. Please ensure you have set NLX_API_KEY.[/red]")
            return
        not (
            yes or confirm(f"There are {len(ops)} OPS defined in this module. Would you like to continue?", default="y")
        ) and exit(1)

        for method, kwargs in ops:
            op = getattr(client, method)
            handler(op, **kwargs)

    @staticmethod
    def config():
        """
        Display the current config as json
        :return:
        """
        return json.dumps(settings.env, indent=2, default=str)


def main():
    fire.Fire(Runner)


if __name__ == "__main__":
    main()
