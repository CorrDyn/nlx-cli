import logging
import os
import sys
from pathlib import Path

import dotenv
import rich

from nlx.utils.dict_utils import DictNamespace
from nlx.utils.module_loading import cached_import
from nlx.utils.settings_utils import once, string_to_bool, string_to_list

DEFAULTS = DictNamespace(
    NLX_ENV_PATH=Path(".env"),
    NLX_SUPPRESS_ENV_NOTICE=False,
    NLX_LOG_LEVEL="DEBUG",
    NLX_API_KEY="12",
    NLX_API_URL="https://api.nlxresearchhub.org",
    NLX_REPORT_HISTORY_STORAGE=Path("nlx.pickle"),
    NLX_REPORT_DOWNLOAD_DIR=".reports",
)

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())

NLX_ENV_PATH = Path(os.environ.get("NLX_ENV_PATH", DEFAULTS["NLX_ENV_PATH"]))
dotenv.load_dotenv(NLX_ENV_PATH, override=True)


def get_runtime_parameters(defaults):
    cleaned = {}
    for key, default in defaults.items():
        if isinstance(default, (list, tuple, set)):
            cleaned[key] = string_to_list(os.environ.get(key, default))
        elif isinstance(default, bool):
            cleaned[key] = string_to_bool(os.environ.get(key, default))
        else:
            # e.g., Path('.env') in default will create a Path from the environment setting
            cleaned[key] = type(default)(os.environ.get(key, default))
    return DictNamespace(**cleaned)


env = get_runtime_parameters(DEFAULTS)

NLX_SUPPRESS_ENV_NOTICE = env.NLX_SUPPRESS_ENV_NOTICE
NLX_LOG_LEVEL = env.NLX_LOG_LEVEL
NLX_API_KEY = env.NLX_API_KEY
NLX_API_URL = env.NLX_API_URL
NLX_REPORT_HISTORY_STORAGE = env.NLX_REPORT_HISTORY_STORAGE
NLX_REPORT_DOWNLOAD_DIR = env.NLX_REPORT_DOWNLOAD_DIR

logger.setLevel(cached_import("logging", NLX_LOG_LEVEL))

if not NLX_SUPPRESS_ENV_NOTICE and NLX_ENV_PATH.exists():
    once(rich.print)(
        f"[red]Using settings defined in {NLX_ENV_PATH} combined with your environment. "
        f"Suppress this notice with NLX_SUPPRESS_ENV_NOTICE=True [/red]",
        file=sys.stderr,
    )
elif not NLX_SUPPRESS_ENV_NOTICE:
    once(rich.print)(
        f"[red]Using settings defined in your environment. "
        f"Suppress this notice with NLX_SUPPRESS_ENV_NOTICE=True[/red]",
        file=sys.stderr,
    )
