import datetime

import fire
from dateutil.relativedelta import relativedelta


class helpers:
    @staticmethod
    def calendar_year(year: int, format="%Y-%m-%d"):
        """
        For a given year, produce a list of start and end times for each month.
        :param year: calendar year
        :param format: desired string format of output dates
        :return:
        """
        dates = []
        start = datetime.date(year, 1, 1)
        end = start + relativedelta(months=1)
        # increase the start and end one month at a time until we are in the next year
        # or until we reach an end date in the future
        while start.year < year + 1 and end < datetime.date.today():
            # the API filtering is inclusive on the start and exclusive on the end,
            # e.g. the range [2021-03-01, 2021-04-01) will not include 2021-04-01.
            dates.append(dict(start=start.strftime(format), end=end.strftime(format)))
            start += relativedelta(months=1)
            end += relativedelta(months=1)
        return dates

    @staticmethod
    def generate_year_kwargs(year: int, **kwargs):
        """
        For a given year, produce a list of start and end times, plus any other keyword
        E.g.:
            generate_year_kwargs(2021, auto=True, state="KS") =>
                [
                    {"start": "2021-01-01", "end": "2021-02-01", "auto": True, "state":"KS"},
                    {"start": "2021-02-01", "end": "2021-03-01", "auto": True, "state":"KS"},
                    . . .
                ]

        arguments, for each month.
        :param year: calendar year
        :param kwargs: other keyword arguments to be added to the list
        :return:
        """
        _kwargs = []
        for date in helpers.calendar_year(year):
            _kwargs.append({**date, **kwargs})
        return _kwargs


if __name__ == "__main__":
    fire.Fire(helpers)
