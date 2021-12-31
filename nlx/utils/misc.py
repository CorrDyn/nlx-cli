from urllib.parse import urlparse

from rich.prompt import Prompt


def confirm(question, color="cyan"):
    response = Prompt.ask(f"[{color}]{question} (y/N)#[/{color}]")
    return response.lower() in ["y", "yes"]


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
