import ujson
from audioop import add
import sqlite3
from contextlib import contextmanager
import yaml

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

print = __import__("rich").print
import weakref


class Observer(object):
    """Observes attached data and trigger out given action if the content of data changes.
    Observer is a descriptor, which means, it must be declared on the class definition level.

    Example:
        >>> def action(observer, instance, value):
        ...     print 'Data has been modified: %s' % value

        >>> class MyClass(object):
        ...     important_data = Observer('init_value', callback=action)

        >>> o = MyClass()
        >>> o.important_data = 'new_value'
        Data has been modified: new_value


    Observer should work with any kind of built-in data types, but `dict` and `list` are strongly advice.

    Example:
        >>> class MyClass2(object):
        ...     important_data = Observer({}, callback=action)
        >>> o2 = MyClass2()
        >>> o2.important_data['key1'] = {'item1': 'value1', 'item2': 'value2'}
        Data has been modified: {'key1': {'item2': 'value2', 'item1': 'value1'}}
        >>> o2.important_data['key1']['item1'] = range(5)
        Data has been modified: {'key1': {'item2': 'value2', 'item1': [0, 1, 2, 3, 4]}}
        >>> o2.important_data['key1']['item1'][0] = 'first'
        Data has been modified: {'key1': {'item2': 'value2', 'item1': ['first', 1, 2, 3, 4]}}


    Here is an example of using `Observer` as a base class.

    Example:
        >>> class AdvanceDescriptor(Observer):
        ...     def action(self, instance, value):
        ...         logger = instance.get_logger()
        ...         logger.info(value)
        ...
        ...     def __init__(self, additional_data=None, **kwargs):
        ...         self.additional_data = additional_data
        ...
        ...         super(AdvanceDescriptor, self).__init__(
        ...             callback=AdvanceDescriptor.action,
        ...             init_value={},
        ...             additional_data=additional_data
        ...         )
    """

    def __init__(self, init_value=None, callback=None, **kwargs):
        """
        Args:
            init_value: initial value for data, if there is none
            callback: callback function to evoke when the content of data will change; the signature of
                the callback should be callback(observer, instance, value), where:
                    observer is an Observer object, with all additional data attached to it,
                    instance is an instance of the object, where the actual data lives,
                    value is the data itself.
            **kwargs: additional arguments needed to make inheritance possible. See the example above, to get an
                idea, how the proper inheritance should look like.
                The main challenge here comes from the fact, that class constructor is used inside the class methods,
                which is quite tricky, when you want to change the `__init__` function signature in derived classes.
        """
        self.init_value = init_value
        self.callback = callback
        self.kwargs = kwargs
        self.kwargs.update(
            {
                "callback": callback,
            }
        )

        self._value = None

        self._instance_to_name_mapping = {}
        self._instance = None

        self._parent_observer = None

        self._value_parent = None
        self._value_index = None

    @property
    def value(self):
        """Returns the content of attached data."""
        return self._value

    def _get_attr_name(self, instance):
        """To respect DRY methodology, we try to find out, what the original name of the descriptor is and
        use it as instance variable to store actual data.

        Args:
            instance: instance of the object

        Returns: (str): attribute name, where `Observer` will store the data
        """
        if instance in self._instance_to_name_mapping:
            return self._instance_to_name_mapping[instance]
        for attr_name, attr_value in instance.__class__.__dict__.items():
            if attr_value is self:
                self._instance_to_name_mapping[weakref.ref(instance)] = attr_name
                return attr_name

    def __get__(self, instance, owner):
        attr_name = self._get_attr_name(instance)
        attr_value = instance.__dict__.get(attr_name, self.init_value)

        observer = self.__class__(**self.kwargs)
        observer._value = attr_value
        observer._instance = instance
        return observer

    def __set__(self, instance, value):
        attr_name = self._get_attr_name(instance)
        instance.__dict__[attr_name] = value
        self._value = value
        self._instance = instance
        self.divulge()

    def __getitem__(self, key):
        observer = self.__class__(**self.kwargs)
        observer._value = self._value[key]
        observer._parent_observer = self
        observer._value_parent = self._value
        observer._value_index = key
        return observer

    def __setitem__(self, key, value):
        self._value[key] = value
        self.divulge()

    def divulge(self):
        """Divulges that data content has been change calling callback."""
        # we want to evoke the very first observer with complete set of data, not the nested one
        if self._parent_observer:
            self._parent_observer.divulge()
        else:
            if self.callback:
                self.callback(self, self._instance, self._value)

    def __getattr__(self, item):
        """Mock behaviour of data attach to `Observer`. If certain behaviour mutate attached data, additional
        wrapper comes into play, evoking attached callback.
        """

        def observe(o, f):
            def wrapper(*args, **kwargs):
                result = f(*args, **kwargs)
                o.divulge()
                return result

            return wrapper

        attr = getattr(self._value, item)

        if item in (
            ["append", "extend", "insert", "remove", "pop", "sort", "reverse"]
            + ["clear", "pop", "update"]  # list methods  # dict methods
        ):
            return observe(self, attr)
        return attr


def create_autoyaml(name, get_load=True, get_save=False, ):
    def action(self, instance, value):
        with open(name, "w") as f:
            yaml.dump(value, f, Dumper=Dumper)
            
    class AutoYaml(object):
        data = Observer('', action)

    auto = AutoYaml()
    try:
        with open(name, "r") as f:
            auto.data = yaml.load(f, Loader=Loader)
    except FileNotFoundError:
        auto.data = {}
    
    returned = [auto]
    if get_load:
        def load():
            with open(name, "r") as f:
                auto.data = yaml.load(f, Loader=Loader)
        returned.append(load)
    if get_save:
        def save():
            with open(name, "w") as f:
                yaml.dump(dict(auto.data), f, Dumper=Dumper)
        returned.append(save)
    return returned
    
    
class ColumnAttribute:
    def __init__(
        self,
        name,
        type,
        default=None,
        primary_key=False,
        auto_increment=False,
        unique=False,
        index=False,
    ):
        self.name = name
        self.type = type
        self.default = default
        self.primary_key = primary_key
        self.auto_increment = auto_increment
        self.unique = unique
        self.index = index

    def to_sql(self):
        additional = "DEFAULT {}".format(self.default) if self.default else ""
        if self.primary_key:
            additional += " PRIMARY KEY"
        if self.auto_increment:
            additional += " AUTOINCREMENT"
        if self.unique:
            additional += " UNIQUE"
        if self.index:
            additional += " INDEX"
        return "{} {} {}".format(self.name, self.type, additional)

    @classmethod
    def from_sql(cls, sql):
        name, type, additional = sql.split(" ", 2)
        additional = additional.split()
        primary_key = "PRIMARY KEY" in additional
        auto_increment = "AUTOINCREMENT" in additional
        unique = "UNIQUE" in additional
        index = "INDEX" in additional
        return cls(
            name,
            type,
            primary_key=primary_key,
            auto_increment=auto_increment,
            unique=unique,
            index=index,
        )

    @classmethod
    def from_dict(self, dict):
        """
        {
            "pos": ["INTEGER", "PRIMARY KEY", "AUTOINCREMENT", "UNIQUE"],
            "id": ["INTEGER", "UNIQUE"],
            "name": "Alex",
            "age": 25,
            "city": "Moscow",
            "rate": 5.5,
            "uuid": ["TEXT", "UNIQUE"],
        } ->
        [
            ColumnAttribute('id', 'INTEGER', primary_key=True, auto_increment=True),
            ColumnAttribute('name', 'TEXT'),
            ColumnAttribute('age', 'INTEGER'),
            ColumnAttribute('city', 'TEXT'),
            ColumnAttribute('rate', 'REAL'),
            ColumnAttribute('description', 'TEXT', default='Lorem ipsum'),
            ColumnAttribute('uuid', 'TEXT', unique=True)
        ]
        """
        columns = []
        for key, value in dict.items():
            if isinstance(value, str):
                column_type = "TEXT"
                columns.append(ColumnAttribute(key, column_type, default=value))
            elif isinstance(value, int):
                column_type = "INTEGER"
                columns.append(ColumnAttribute(key, column_type, default=value))
            elif isinstance(value, float):
                column_type = "REAL"
                columns.append(ColumnAttribute(key, column_type, default=value))
            elif isinstance(value, bool):
                column_type = "INTEGER"
                columns.append(ColumnAttribute(key, column_type, default=int(value)))
            elif isinstance(value, list):
                if all(
                    [
                        item in ["PRIMARY KEY", "AUTOINCREMENT", "UNIQUE"]
                        for item in value[1:]
                    ]
                ) and value[0] in ["INTEGER", "REAL", "TEXT"]:
                    column_type = value[0]
                    primary_key = True if "PRIMARY KEY" in value else False
                    auto_increment = True if "AUTOINCREMENT" in value else False
                    unique = True if "UNIQUE" in value else False
                    columns.append(
                        ColumnAttribute(
                            key,
                            column_type,
                            primary_key=primary_key,
                            auto_increment=auto_increment,
                            unique=unique,
                        )
                    )
                else:
                    column_type = "TEXT"
                    additional = ujson.dumps(value)
                    columns.append(
                        ColumnAttribute(key, column_type, default=additional)
                    )
            elif isinstance(value, dict):
                column_type = "TEXT"
                additional = ujson.dumps(value)
                columns.append(ColumnAttribute(key, column_type, default=additional))
        return columns

    def __repr__(self):
        return "<ColumnAttribute {}>".format(self.name)


class Columns:
    def __init__(self, columns):
        """
        {
            "name": ColumnAttribute,
            ...
        }
        """
        self.columns = columns

    def to_sql(self):
        return ", ".join(column.to_sql() for column in self.columns.values())


class Table:
    def __init__(self, cursor, name):
        self.cursor = cursor
        self.name = name

    def insert(self, *data):
        """
        insert({"name": "Alex", "age": 25, "city": "Moscow", "rate": 5.5, "description": "Lorem ipsum", "uuid": "123456789"})
        """
        columns = ", ".join(data[0].keys())
        values = ", ".join(["?"] * len(data[0]))
        sql = "INSERT INTO {} ({}) VALUES ({})".format(self.name, columns, values)
        self.cursor.execute(sql, [data[0][key] for key in data[0].keys()])
        return self.cursor.lastrowid

    def get(self, order=None, limit=None, offset=None, **kwargs):
        additional = ""
        if order:
            additional += "ORDER BY {} DESC".format(order)
        if limit:
            additional += " LIMIT {}".format(limit)
        if offset:
            additional += " OFFSET {}".format(offset)
        sql = "SELECT * FROM {} {}".format(self.name, additional)
        self.cursor.execute(sql)
        return self.cursor.fetchall()


class SimpleBase:
    def __init__(self, name):
        self.name = name
        self.connection = sqlite3.connect(self.name)
        self.cursor = self.connection.cursor()

    def __del__(self):
        self.connection.close()

    def create_table(self, table_name, columns):
        columns = ", ".join([column.to_sql() for column in columns])
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS {} ({})".format(table_name, columns)
        )
        self.connection.commit()
        return Table(self.cursor, table_name)

class StorageManager:
    def __init__(self, name):
        self.observer, self.load, self.save = create_autoyaml('t', get_save=True)
    

