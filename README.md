## Installation
Clone the repository and use pip to install it into a python environment, e.g.
```bash
git clone https://github.com/CorrDyn/nlx-cli
python3.7 -m venv venv
source ./venv/bin/activate
pip install ./nlx-cli
```

## Configuration
You can configure cli settings with a .env file and/or environment variables.
The only configuration you will need to modify out of the box is `NLX_API_KEY`.
To list the current active configuration, you can use the `config` command:
```bash
nlx config | jq
{
  "NLX_ENV_PATH": ".env",
  "NLX_SUPPRESS_ENV_NOTICE": true,
  "NLX_LOG_LEVEL": "INFO",
  "NLX_API_KEY": "<redacted>",
  "NLX_API_URL": "https://api.nlxresearchhub.org",
  "NLX_REPORT_HISTORY_STORAGE": "nlx.pickle",
  "NLX_REPORT_DOWNLOAD_DIR": ".reports"
}
```

## Usage
You can use any access methods defined directly by the CLI or you can define a custom
runner module. For details on CLI methods, you can run `nlx --help`.

### Custom Runner Module
Custom runner modules allow you to specify a client class and a list of operations to perform with
that client class. Custom runner modules must define the following:
- `RUNNER_CLIENT` python module style import path to your Client class definition
- `RUNNER_OPS` list of operations which will be performed by your client

Below is an example of a custom runner module (the current revision of which can be found in [./examples/example_run_config.py](./examples/example_run_config.py)).
To run this example, copy the contents of the runner into a `example_run_config.py` in you current working directory
and execute the command `nlx run example_run_config`. To preview the operations that this will run, you can use
`nlx show_ops example_run_config`

```python
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
```

### Programmatic Usage
If custom runner modules don't provide enough flexibility for your use-case, you can always import anything
available in the nlx-cli package for use as you see fit.
```python
from nlx.client import AsyncReport

assert AsyncReport().is_authorized
```
