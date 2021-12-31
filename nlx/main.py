#!/usr/bin/env python
import json
import os
import sys

import fire
import rich

from nlx.client import AsyncReport
from nlx.conf import settings
from nlx.utils.misc import confirm
from nlx.utils.module_loading import cached_import, import_string


class Runner:
    async_report = AsyncReport

    @staticmethod
    def run(run_config, yes=False):
        """
        Execute a python module as a series of API Calls
        :param run_config: python import module path containing the run config
        :param yes: auto-confirm any prompts
        :return:
        """
        # ensure modules in the user's current directory are importable
        sys.path.insert(0, os.getcwd())
        ClientClass = import_string(str(cached_import(run_config, "RUNNER_CLIENT")))
        client = ClientClass()
        if not client.is_authorized:
            rich.print("[red]Client could not be authenticated. Please ensure you have set NLX_API_KEY.[/red]")
            return
        OPS = cached_import(run_config, "RUNNER_OPS")
        not (yes or confirm(f"There are {len(OPS)} OPS defined in this module. Would you like to continue?")) and exit(
            0
        )

        for method, kwargs in OPS:
            op = getattr(client, method)
            op(**kwargs)

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
