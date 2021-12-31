import logging
from urllib.parse import urlparse

from rich.prompt import Prompt

from nlx.utils.module_loading import cached_import


def confirm(question, color="cyan", default="n"):
    default = default.lower()
    yes = ["y", "yes"]
    prompt = "(Y/n)" if default in yes else "(y/N)"
    response = Prompt.ask(f"[{color}]{question} {prompt}[/{color}]")
    response = response.lower() if response else default
    return response in ["y", "yes"]


def basic_logger(name, level):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("[%(levelname)s] [%(asctime)s] [%(name)s;%(filename)s:%(lineno)d] - %(message)s")
    )
    logger.addHandler(handler)
    return logger


class URL:
    url = None

    def __init__(self, url):
        if isinstance(url, URL):
            self.url = url.url
            return
        try:
            parsed = urlparse(url)
            self.url = url
            assert all([parsed.scheme, parsed.netloc])
        except (ValueError, AssertionError):
            raise ValueError(f"{url} could not be parsed as a valid url")

    def __str__(self):
        return str(self.url)


class LogLevel:
    level = "DEBUG"

    def __init__(self, level):
        if isinstance(level, LogLevel):
            self.level = level.level
            return
        try:
            cached_import("logging", level)
            self.level = level
        except AttributeError:
            raise ValueError(f"{level} could not be parsed as a valid log level.")

    def __str__(self):
        return str(self.level)


def cast(value, func):
    res = None
    try:
        res = func(value)
    except:  # noqa
        return res, False
    return res, True
