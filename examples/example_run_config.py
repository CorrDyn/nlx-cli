from nlx.helpers import helpers

RUNNER_CLIENT = "nlx.client.AsyncReport"

YEARS = [*range(2017, 2021)]
STATES = ["KS"]

RUNNER_OPS = []
for state in STATES:
    for year in YEARS:
        for kwargs in helpers.generate_year_kwargs(year, state=state, auto=True):
            RUNNER_OPS.append(("create", kwargs))
