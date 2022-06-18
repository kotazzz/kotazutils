import shlex
from rich.console import Console
from prompt_toolkit import ANSI, PromptSession

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
from rich.text import Text
import io
#! move to top ################################################################


def mark_to_ansi(text, console=None):
    if console is None:
        console = Console(file=io.StringIO(), force_terminal=True)
    console.print(text, markup=True, end='')
    val = console.file.getvalue()
    console.file.seek(0)
    return ANSI(val)



class HashableCompletion(Completion):
    def __hash__(self):
        return hash((self.text, id(self)))
    
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
    def update_completions(self, data):
        self.completions = data

    
    def get_completions(self, document, complete_event):
        words = shlex.split(document.text_before_cursor)
        last_word = words[-1] if words else ""
        completions = self.completions
        text = document.text_before_cursor
        def data_to_completion(data):
            return Completion(data.text.lstrip(last_word), display=data.display, display_meta=data.meta)
        def get_completions_for_word(word, completions, remain_words):
            # print(word, completions, remain_words)
            possible = {}
            if completions:
                if isinstance(completions, set):
                    completions = {completion: None for completion in completions}
                for completion, nested in completions.items():
                    if completion.text.startswith(word):
                        possible[completion] = nested
                    if word == completion.text:
                        if remain_words:
                            return get_completions_for_word(remain_words.pop(0), nested, remain_words)
                        elif text.endswith(' ') and nested:
                            return nested.keys() if isinstance(nested, dict) else list(nested)
            return possible
        if words:
            c = get_completions_for_word(words.pop(0), completions, words)
            for data in c:
                completion = data_to_completion(data)
                yield completion
        else:
            for completion in completions:
                yield data_to_completion(completion)

class RichCompletion:
    def __init__(self, text, display, meta):
        self.text = text
        self.display = mark_to_ansi(display)
        self.meta = mark_to_ansi(meta)
    
    
completions = {
    RichCompletion("echo", "[bold]echo[/] <'test' \[text]|text>", "Выводит текст", ): {
        RichCompletion("test", "[bold]test[/] \[text]", "Выводит тестовый текст", )
        },
    RichCompletion("echo2", "[bold]echo2[/] <Обязательный|'Подкоманда' \[Необязательный арг подкоманды]>", "Тестовая команда", ): None
    }

c = MyCustomCompleter()
c.update_completions(completions)

session = PromptSession('> ', completer=c)
text = session.prompt()
