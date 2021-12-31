"""
This runner will create, await, and download async reports for all job listings
compiled in the years 2017-2021 for Kansas.

You want to place this file in your current working directory or a location that
is importable from your current python path.
"""

from nlx.helpers import helpers

# python module style import path of the Client class to be executed by the runner.
RUNNER_CLIENT = "nlx.client.AsyncReport"

# years 2017-2021, inclusive
YEARS = [*range(2017, 2021)]
# Kansas
STATES = ["KS"]

RUNNER_OPS = []
for state in STATES:
    for year in YEARS:
        # generate twelve months of the arguments for start, end, state, auto
        for kwargs in helpers.generate_year_kwargs(year, state=state, auto=True):
            # indicate that the kwargs will be passed to RUNNER_CLIENT.create, e.g.
            # nlx.client.AsyncReport().create(**kwargs)
            RUNNER_OPS.append(("create", kwargs))
