from rich.prompt import Prompt


def confirm(question, color="cyan"):
    response = Prompt.ask(f"[{color}]{question} (y/N)#[/{color}]")
    return response.lower() in ["y", "yes"]
