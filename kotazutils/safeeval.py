import ast
import operator as op

class EvalProcessor:
    """Процессор вычисления математических выражений с поддержкой вызовов функций и переменных"""

    def __init__(self):
        """Инициализация процессора"""
        self.default_environment = {}
        self.environment = self.reset_environment()
        self.avaliable_operators = {
            ast.Add: op.add,
            ast.Sub: op.sub,
            ast.Mult: op.mul,
            ast.Div: op.truediv,
            ast.Pow: op.pow,
            ast.BitXor: op.xor,
            ast.USub: op.neg,
            ast.MatMult: op.matmul,
        }

    def reset_environment(self):
        """Сбрасывает окружение"""
        self.environment = self.default_environment

    def set_default_environment(self, environment):
        """Устанавливает окружение по умолчанию"""
        self.default_environment = environment

    def node_eval(self, node, environment: dict):
        """Вычисляет одно выражение"""
        operators = self.avaliable_operators

        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.BinOp):
            return operators[type(node.op)](
                self.node_eval(node.left, environment=environment),
                self.node_eval(node.right, environment=environment),
            )
        elif isinstance(node, ast.UnaryOp):
            return operators[type(node.op)](
                self.node_eval(node.operand, environment=environment)
            )
        elif isinstance(node, ast.Name):
            return environment[node.id]
        elif isinstance(node, ast.Call):
            return self.node_eval(node.func, environment)(
                *map(lambda n: self.node_eval(n, environment), node.args)
            )
        elif isinstance(node, ast.Subscript):
            return self.node_eval(node.value, environment)[
                self.node_eval(node.slice, environment)
            ]
        else:
            raise Exception("invalid eval type: ", node)

    def eval_expression(self, expr: str, environment=None):
        """Вычисляет большое выражение"""
        if environment is None:
            environment = self.environment

        return self.node_eval(ast.parse(expr, mode="eval").body, environment)
