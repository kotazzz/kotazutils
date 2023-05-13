import shlex
from prompt_toolkit import ANSI, PromptSession
import inspect
from prompt_toolkit.completion import Completer, Completion
from rich.console import Console
import io
import lark
class Command:
    def __init__(self, name):
        self.name = name
        self.arguments = []
    
    def run(self):
        pass
    
    def __call__(self, function):
        self.function = function
        return self
    

@Command('help')
def help_():
    print(123)

class RichPromptBridge:
    def __init__(self):
        self.console = Console(file=io.StringIO(), force_terminal=True)
    
    def markup_to_ansi(self, text):
        self.console.print(text, markup=True, end="")
        val = self.console.file.getvalue()
        self.console.file.seek(0)
        return ANSI(val)
    

class RichCompletion:
    def __init__(self, text, display, meta):
        self.bridge = RichPromptBridge()
        self.text = text
        self.display = self.bridge.markup_to_ansi(display)
        self.meta = self.bridge.markup_to_ansi(meta)


cmd = "cmd sub --flag 132 12.3 -3 --flag=2"

grammar = """
start: word*

word: value | flag | min_flag
value: number | string | dt_all
flag: "--" CNAME ("=" value)?
min_flag: "-"  (" " value)?

dt_all: date | time | datetime

string: CNAME | ESCAPED_STRING
number: SIGNED_NUMBER
date: DATE
time: TIME
datetime: DATETIME
// Done from a readthrough of the https://en.wikipedia.org/wiki/ISO_8601
// Could be made more robust, to not parse invalid dates

// Date primitives
YEAR  : DIGIT DIGIT DIGIT DIGIT
MONTH : "0" "1".."9"
      | "1" "1".."2" 
DAY   : "0" DIGIT
      | "1" DIGIT 
      | "2" DIGIT
      | "3" "0".."1" 

// Dates
CALENDAR_DATE : YEAR "-"? MONTH "-"? DAY
              | YEAR "-" MONTH
              | "--" MONTH "-"? DAY

WEEK_NUMBER          : "0".."4" DIGIT
                     | "5" "0".."3"
PREFIXED_WEEK_NUMBER : "W" WEEK_NUMBER
WEEKDAY_NUMBER       : "1".."7"
WEEK_DATE            : YEAR "-"? PREFIXED_WEEK_NUMBER
                     | YEAR "-"? PREFIXED_WEEK_NUMBER "-"? WEEKDAY_NUMBER

DAY_NUMBER   : "1".."2" DIGIT    DIGIT
             | "3"      "0".."5" DIGIT
             | "3"      "6"      "0".."6" // leap day
ORDINAL_DATE : YEAR "-"? DAY_NUMBER

DATE : ORDINAL_DATE 
     | CALENDAR_DATE 
     | WEEK_DATE

// Time primitives
HOUR         : "0".."1" DIGIT
             | "2" "0".."4"
MINUTE       : "0".."5" DIGIT
SECOND       : "0".."5" DIGIT 
             | "60" // leap second
FRACTIONAL   : "." DIGIT+

// Time
TIME         : "T"? HOUR ":"? MINUTE ":"? SECOND FRACTIONAL?
PREFIXED_TIME: "T" HOUR ":"? MINUTE ":"? SECOND FRACTIONAL?
TIME_ZONE    : "Z"
             | ("+"|"-") HOUR (":"? MINUTE)

// Combined
DATETIME     : DATE PREFIXED_TIME TIME_ZONE?

%import common.ESCAPED_STRING
%import common.SIGNED_NUMBER
%import common.CNAME
%import common.WS
%import common.C_COMMENT  
%import common.DIGIT  
%ignore WS
%ignore C_COMMENT
"""
class KotazyTransformer(lark.Transformer):
    def start(self, d):
        return d
    def word(self, d):
        return d
    def value(self, d):
        return d
    def flag(self, d):
        return d
    def min_flag(self, d):
        return d
    def year(self, d):
        ку

p = lark.Lark(grammar, start="start")
p.parse("cmd sub --flag 132 12.3 -3 --flag=2 -f x")