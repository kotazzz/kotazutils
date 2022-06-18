from rich.console import Console
from prompt_toolkit import PromptSession

from prompt_toolkit.completion import Completer, Completion


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

class Command:
    def __init__(self, name, brief='This is brief', description='This is description'):
        self.name = name
        self.brief = brief
        self.description = description

    def __call__(self, function):
        self.function = function
        return self

    def check_args(self, *args):
        for i, required_type in enumerate(get_type_hints(self.function).values()):
            if required_type is not None:
                if type(args[i]) is not required_type:
                    return i, type(args[i]), required_type
                    

    def callback(self, *args):
        return self.function(self, *args)

@Command("echo", "Echo", "Echo something")
def echo(self, text: str, times: int = 2, without_hello: bool = False):
    text = "Hello, " + text if not without_hello else text
    return ', '.join([text] * times)

print(echo.callback("Hello", 3, True))

def test(a: int|str): pass
print(get_type_hints(test))

class MyCustomCompleter(Completer):
    def get_completions(self, document, complete_event):
        yield Completion('completion', start_position=0)


session = PromptSession('> ', completer=MyCustomCompleter())
#text = session.prompt()
