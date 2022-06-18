import inspect
from typing import get_type_hints
import io
import shlex
from rich.console import Console
from prompt_toolkit import ANSI, PromptSession

from prompt_toolkit.completion import Completer, Completion


def mark_to_ansi(text, console=None):
    # TODO: may be move to utils?
    if console is None:
        console = Console(file=io.StringIO(), force_terminal=True)
    console.print(text, markup=True, end="")
    val = console.file.getvalue()
    console.file.seek(0)
    return ANSI(val)


def get_args(func, exclude_self=True):
    signature = inspect.signature(func)
    return [
        (i, k)
        for i, (k, v) in enumerate(signature.parameters.items())
        if k != "self" or not exclude_self
    ]


def get_default_args(func):
    signature = inspect.signature(func)
    return {
        k: v.default
        for k, v in signature.parameters.items()
        if v.default is not inspect.Parameter.empty
    }


class RichCompletion:
    def __init__(self, text, display, meta):
        self.text = text
        self.display = mark_to_ansi(display)
        self.meta = mark_to_ansi(meta)


class RichCompleter(Completer):
    def update_completions(self, data):
        self.completions = data

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        words = shlex.split(text)
        last_word = words[-1] if words else ""
        completions = self.completions

        def data_to_completion(data):
            return Completion(
                data.text.lstrip(last_word),
                display=data.display,
                display_meta=data.meta,
            )

        def get_completions_for_word(word, completions, remain_words):
            # print(word, completions, remain_words)
            possible = {}
            if completions:
                if isinstance(completions, set | list):
                    completions = {completion: None for completion in completions}
                for completion, nested in completions.items():
                    if completion.text.startswith(word):
                        possible[completion] = nested
                    if word == completion.text:
                        if remain_words:
                            return get_completions_for_word(
                                remain_words.pop(0), nested, remain_words
                            )
                        elif text.endswith(" ") and nested:
                            return (
                                nested.keys()
                                if isinstance(nested, dict)
                                else list(nested)
                            )
            return possible

        if words:
            c = get_completions_for_word(words.pop(0), completions, words)
            for data in c:
                completion = data_to_completion(data)
                yield completion
        else:
            for completion in completions:
                yield data_to_completion(completion)


class Command:
    def __init__(
        self,
        name,
        brief="This is brief",
        description="This is description",
        arg_help=None,
    ):
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

    def try_autocast(self, *args):
        """
        >>> try_autocast("1", "true", "String", "1.02")
        1, True, "String", 1.02
        """
        casters = {
            int: lambda x: int(x) if x.isdigit() else x,
            float: lambda x: float(x) if x.replace(".", "").isdigit() else None,
            bool: lambda x: True if x.lower() == "true" else False,
        }
        new_values = {}
        for i, (name, hint) in enumerate(get_type_hints(self.function).items()):
            if i > len(args) - 1:
                break
            if hint in casters:
                new_value = casters[hint](args[i])
                if new_value is not None:
                    new_values[name] = new_value
            else:
                new_values[name] = args[i]
        return new_values

    def callback(self, *args):
        try:
            all_args = get_args(self.function)
            non_hinted = [
                args[i - 1]
                for i, arg in all_args
                if get_type_hints(self.function).get(arg) is None
            ]
            return self.function(
                self, *non_hinted, **self.try_autocast(*args[len(non_hinted) :])
            )
        except Exception as e:
            return self.function(self, *args)

    def required(self):
        all_args = get_args(self.function)
        hinted = [
            arg
            for i, arg in all_args
            if get_type_hints(self.function).get(arg) is not None
        ]
        default_values = get_default_args(self.function)
        # return hinted args without default value
        return [arg for arg in hinted if default_values.get(arg) is None]

    def subcommand(
        self, name, brief="This is brief", description="This is description"
    ):
        command = Command(name, brief, description)
        self.subcommands.append(command)
        return command

    def make_rich_completion(self):

        type_hints = get_type_hints(self.function)
        default_args = get_default_args(self.function)
        parametrs = []
        for key, value in type_hints.items():
            parametrs.append(
                f'<{key}:{value.__name__}{"="+repr(v) if (v:=default_args.get(key)) else ""}>'
            )
        nested_completion = {}

        for command in self.subcommands:
            parametrs[0] = parametrs[0][0] + f"{command.name}|" + parametrs[0][1:]
            nested_completion |= command.make_rich_completion()

        return {
            RichCompletion(
                self.name, f'[b]{self.name}[/] {" ".join(parametrs)}', self.brief
            ): nested_completion
        }


class CliApp:
    def __init__(self, name, description="CLI App", version="1.0.0"):
        self.name = name
        self.description = description
        self.version = version

        self.commands = {}
        self.toolbar_handlers = []
        self.right = None
        self.prompt = lambda *args: "> "

        self.console = Console()
        self.session = PromptSession(self.prompt)
        self.completer = RichCompleter()
        self.state = "init"

    def exit_command(self):
        self.console.print("Bye!")
        self

    def add_command(self, command):
        self.commands[command.name] = command

    def command(self, name, brief="This is brief", description="This is description"):
        command = Command(name, brief, description)
        self.add_command(command)
        return command

    def get_completions(self):
        result = {}
        for command in self.commands.values():
            result |= command.make_rich_completion()
        return result

    def run(self):
        self.state = "run"

        def get_command(args, commands, prev=None):
            for command in commands:
                if command.name == args[0]:
                    if len(args) > 1:
                        return get_command(args[1:], command.subcommands, command)
                    else:
                        return command, args[1:]
            return prev, *args

        while self.state == "run":
            try:
                self.completer.update_completions(self.get_completions())
                text = self.session.prompt("> ", completer=self.completer)
                full_command = shlex.split(text)
                if not text:
                    continue
                else:
                    cmd, *args = get_command(full_command, self.commands.values())
                    if cmd:
                        if args == [[]]:
                            args = []
                        required = cmd.required()
                        if len(required) > len(args):
                            required_count = len(required) - len(args)
                            required_sequence = ", ".join(required[len(args) :])
                            self.console.print(
                                f"{cmd.name} requires {required_count} more arguments: {required_sequence}"
                            )
                            continue
                        cmd.callback(self, *args)
                    else:
                        self.console.print("Unknown command")
            except EOFError:
                self.state = "exit"
            except KeyboardInterrupt:
                self.console.print("Используйте Ctrl+D для выхода")
            except Exception:
                self.console.print_exception()


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
