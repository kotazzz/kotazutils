import shlex
from prompt_toolkit import ANSI, PromptSession
import inspect

class Command:
    def __init__(self, name):
        self.name = name
    
    def run(self):
        pass
    
    def __call__(self, function):
        self.function = function
        return self
    

@Command('help')
def help_():
    print(123)

print(help_)

