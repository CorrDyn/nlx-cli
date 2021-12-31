"""
This runner will create, await, and download async reports for all job listings
compiled in the years 2017-2022 for Kansas.

You want to place this file in your current working directory or a location that
is importable from your current python path.
"""
import logging

from nlx.helpers import helpers
from nlx.utils.misc import basic_logger

logger = basic_logger(__name__, logging.DEBUG)

# python module style import path of the Client class to be executed by the runner.
RUNNER_CLIENT = "nlx.client.AsyncReport"

# years 2017-2022, inclusive
YEARS = [*range(2017, 2023)]
# Kansas
STATES = ["KS"]

RUNNER_OPS = []
for state in STATES:
    for year in YEARS:
        # generate twelve months of the arguments for start, end, state, auto.
        # note that future dates are skipped by generate_year_kwargs.
        for generated_kwargs in helpers.generate_year_kwargs(year, state=state, auto=True):
            # indicate that the kwargs will be passed to RUNNER_CLIENT.create, e.g.
            # nlx.client.AsyncReport().create(**generated_kwargs)
            RUNNER_OPS.append(("create", generated_kwargs))


def error_handler(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except KeyboardInterrupt:
        raise
    except:  # noqa
        logger.exception(f"Something unexpected happened when executing func={func} args={args}, kwargs={kwargs}")


RUNNER_OP_ERROR_HANDLER = error_handler
