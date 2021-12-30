import datetime

import fire
from dateutil.relativedelta import relativedelta


class helpers:
    @staticmethod
    def calendar_year(year: int, format="%Y-%m-%d"):
        dates = []
        start = datetime.date(year, 1, 1)
        end = start + relativedelta(months=1)
        while start.year < year + 1:
            dates.append(dict(start=start.strftime(format), end=end.strftime(format)))
            start += relativedelta(months=1)
            end += relativedelta(months=1)
        return dates

    @staticmethod
    def generate_year_kwargs(year: int, **kwargs):
        _kwargs = []
        for date in helpers.calendar_year(year):
            _kwargs.append({**date, **kwargs})
        return _kwargs


if __name__ == "__main__":
    fire.Fire(helpers)
