from rich.console  import Console

class CliApp:

    def __init__(self, name, description, version):
        self.name = name
        self.description = description
        self.version = version

        self.commands = {}
        self.toolbar_handlers = []
        self.right = None
        self.prompt = lambda *args: "> "

    def run(self):
        pass

    