from rich.console import Console
from prompt_toolkit import PromptSession

from prompt_toolkit.completion import Completer, Completion

class Command:
    def __init__(self, name, brief='This is brief', description='This is description', arg_help=None):
        self.name = name
        self.brief = brief
        self.description = description
        self.arg_help = arg_help if arg_help else {}

        self.subcommands = []

    def __call__(self, function):
        self.function = function
        return self

    def check_args(self, *args):
        errors = []
        for i, required_type in enumerate(get_type_hints(self.function).values()):
            if required_type is not None:
                if type(args[i]) is not required_type:
                    try:
                        args[i] = required_type(args[i])
                    except:
                        errors.append([i, type(args[i]), required_type])      

    def callback(self, *args):
        return self.function(self, *args)

    def subcommand(self, name, brief='This is brief', description='This is description'):
        command = Command(name, brief, description)
        self.subcommands.append(command)
        return command

class CliApp:

    def __init__(self, name, description, version):
        self.name = name
        self.description = description
        self.version = version

        self.commands = {}
        self.toolbar_handlers = []
        self.right = None
        self.prompt = lambda *args: "> "

        self.console = Console()
        self.session = PromptSession(self.prompt)

    def run(self):
        pass

from typing import get_type_hints

#! move to top ################################################################



    
# @Command("echo", "Echo", "Echo something")
# def echo(self, text: str, times: int = 2, without_hello: bool = False):
#     text = "Hello, " + text if not without_hello else text
#     return ', '.join([text] * times)
# 
# @echo.subcommand("test", "Test", "Test something")
# def test(self, text: str = "test"):
#     print("Test: " + text)
# 
# print(echo.callback("Hello", 3, True))
# print(test)
# print(echo.print_help())

class MyCustomCompleter(Completer):
    def get_completions(self, document, complete_event):
        # Display this completion, black on yellow.
        yield Completion('completion1', start_position=0,
                         style='bg:ansiyellow fg:ansiblack')

        # Underline completion.
        yield Completion('completion2', start_position=0,
                         style='underline')

        # Specify class name, which will be looked up in the style sheet.
        yield Completion('completion3', start_position=0,
                         style='class:special-completion')


session = PromptSession('> ', completer=MyCustomCompleter())
#text = session.prompt()
