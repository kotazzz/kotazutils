__version__ = "0.5.2"
__author__ = "Kotaz"
__license__ = "MIT"
__email__ = "semechkagent@gmail.com"

__description__ = """
KotazUtils is a collection of utilities for Python.
"""

# TODO: обновить реализацию класса Graph
# TODO: добавить направленные и взвешенные графы
# TODO: переписать inspect и hint связанные вещи в модуле kotazutils.cli_tools

# DONT FORGET TO ADD CHANGELOG
__changelog__ = """
0.6.0:
    - cliapp изменен на более простой и понятный для пользователя вид
    - Обновлен graph
0.5.2:
    - Новый класс graph
    - Исправлена ошибка с uuid_generator
0.5.1:
    - cli_tool: Добавлена опция raw_format
    - cli_tool: Добавлено [] в значение по умолчанию для опций
    - cli_tool: Добавлена поддержка starred-аргументов (только для raw_format)
    - cli_tool: Изменен формат подсказки синтаксиса
0.5.0:
    - cli_tool: Поддержка нескольких панелей над вводом.
0.4.0:
    - Добавлен модуль `cli_tool`.
"""

# python setup.py bdist_wheel
