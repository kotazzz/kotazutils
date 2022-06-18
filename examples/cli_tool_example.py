from kotazutils.cli_tool import CliApp

c = CliApp("App")


@c.command("echo", "Echo text", "Echo something")
def echo(self, cli, text: str, times: int = 2, without_hello: bool = False):
    text = "Hello, " + text if not without_hello else text
    cli.console.print(", ".join([text] * times))


@echo.subcommand("subcommand", "Echo text", "Echo something")
def echo_subcommand(
    self, cli, first_word: str, text: str, times: int = 2, without_hello: bool = False
):
    text = first_word + ", " + text if not without_hello else text
    cli.console.print(", ".join([text] * times))


@c.command("exit", "Exit from app", "Close this app")
def exit_(self, cli):
    cli.state = "exit"


c.run()