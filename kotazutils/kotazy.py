from lark import *
from .safeeval import EvalProcessor




class KotazyParser:
    """Парсер Котазиланга"""

    def __init__(self):
        """Инициализация парсера"""
        self.grammar = """
        codeblock: "{" (call (";" call)*)? "}" 
        call: id "(" (param ("," param)*)? ")"
        param: number | string | id | call | codeblock
        string: ESCAPED_STRING
        number: SIGNED_NUMBER
        id: CNAME

        %import common.ESCAPED_STRING
        %import common.SIGNED_NUMBER
        %import common.CNAME
        %import common.WS
        %import common.C_COMMENT  
        %ignore WS
        %ignore C_COMMENT
        """
        start_block = "codeblock"
        self.parser = Lark(self.grammar, start=start_block)

    def parse(self, *args, **kwargs):
        """Парсит выражение"""
        return self.parser.parse(*args, **kwargs)


class KotazyTransformer(Transformer):
    """Преобразование Lark-конструкции в словарь-дерево"""

    def codeblock(self, d):
        """Работа с кодом '{...}'"""
        return {"type": "code", "calls": d}

    def call(self, d):
        """Работа с вызовами 'id(...)'"""
        v, *p = d
        return {"type": "call", "name": v["val"], "params": p}

    def param(self, d):
        """Работа с параметрами"""
        return d[0]

    def string(self, s):
        """Работа с строками"""
        (s,) = s
        return {"type": "string", "val": s[1:-1]}

    def number(self, n):
        """Работа с числами"""
        (n,) = n
        return {"type": "number", "val": float(n)}

    def id(self, n):
        """Работа с идентификаторами"""
        (n,) = n
        return {"type": "var", "val": str(n)}


class KotazyFunc:
    """Функция с измененным выводом в консоль"""

    def __init__(self, name, func):
        self.name = name
        self.function = func

    def __call__(self, *args, **kwargs):

        if "_proc" in kwargs:
            return self.function(kwargs["_proc"], *args)
        else:
            return self.function(*args)

    def __repr__(self):
        return "<function {}>".format(self.name)


class KotazyEnvironment(dict):
    """Переопределение вывода в консоль"""

    def __getitem__(self, key):
        # print(key)
        item = dict.__getitem__(self, key)
        if isinstance(item, dict):
            return KotazyEnvironment(item)
        elif isinstance(item, list):
            return [KotazyEnvironment(i) for i in item if isinstance(i, dict)]
        elif callable(item):
            return KotazyFunc(key, item)
        return dict.__getitem__(self, key)


class KotazyProcessor:
    """Выполнение кода"""

    def __init__(self):
        """Инициализация процессора"""
        self.default_environment = {
            "out": lambda *p: print(*self.ast_load_list(p)),
            "set": lambda k, v: self.ast_save(k, v),
            "ret": lambda *v: self.ast_load_list(v)
            if len(v) > 1
            else self.ast_load(v[0]),
            "def": lambda n, c: self.ast_define(n, c),
            "lse": lambda: print(list(self.environment.keys())),
            "fle": lambda: print(self.environment),
        }
        self.reset_environment()

    def reset_environment(self):
        """Сброс среды выполнения"""

        self.environment = KotazyEnvironment(self.default_environment)

    def install_environments(self, data: dict):
        """Изменяет текущую среду и среду по умолчанию"""
        self.environment.update(data)
        self.default_environment.update(data)

    def ast_save(self, name: dict, value: dict):
        """Сохранение значения в среду выполнения"""
        if name["type"] == "var":
            self.environment[name["val"]] = self.ast_load(value)
        else:
            raise Exception("invalid save type: ", name)

    def ast_load(self, obj: dict):
        """Загрузка объекта из среды выполнения"""
        if obj["type"] in ["number", "string"]:
            return obj["val"]
        elif obj["type"] == "var":
            return self.environment[obj["val"]]
        elif obj["type"] == "code":
            return self.run(obj)
        elif obj["type"] == "call":
            return self.ast_run_calls([obj])

    def ast_define(self, name: dict, code: dict):
        """Определение функции"""
        if name["type"] == "var":
            self.environment[name["val"]] = lambda: self.run(code)

    def ast_load_list(self, items: list):
        """Загрузка списка объектов из среды выполнения"""
        return [self.ast_load(item) for item in items]

    def ast_run_calls(self, calls: list):
        """Выполнение кода"""
        for call in calls:
            func_obj = self.environment[call["name"]]
            func_args = func_obj.function.__code__.co_varnames

            value = func_obj(
                *call["params"], **({"_proc": self} if "_proc" in func_args else {})
            )
        return value

    def run(self, tree: dict):
        """Выполнение дерева"""
        return self.ast_run_calls(tree["calls"])


class KotazyRunner:
    """Выполнение кода"""

    def __init__(self):
        """Инициализация универсального процессора"""
        self.parser = KotazyParser()
        self.processor = KotazyProcessor()
        self.transformer = KotazyTransformer()
        self.evaluator = EvalProcessor()
        self.processor.install_environments(
            {
                "clc": lambda s: self.evaluator.eval_expression(s["val"])
                if s["type"] == "string"
                else None,
                "pcl": lambda s: print(
                    self.evaluator.eval_expression(s["val"])
                    if s["type"] == "string"
                    else None
                ),
                "ecl": lambda s: self.evaluator.eval_expression(
                    s["val"], self.processor.environment
                )
                if s["type"] == "string"
                else None,
            }
        )

    def parse(self, string: str):
        """Парсит строку и возвращает объект"""
        return self.parser.parse(string)

    def transform(self, object):
        """Преобразует объект в дерево"""
        return self.transformer.transform(object)

    def execute(self, tree: dict):
        """Выполняет дерево"""
        return self.processor.run(tree)

    def run(self, code: str):
        """Выполняет код"""
        tree = self.parse(code)
        tree = self.transform(tree)
        return self.execute(tree)

    def eval(self, expr: str):
        """Вычисляет выражение"""
        return self.evaluator.eval_expression(expr)

    def set_parser(self, parser):
        """Установка парсера"""
        self.parser = parser

    def set_transformer(self, transformer):
        """Установка трансформера"""
        self.transformer = transformer

    def set_processor(self, processor):
        """Установка процессора"""
        self.processor = processor

    def set_evaluator(self, evaluator):
        """Установка вычислителя"""
        self.evaluator = evaluator