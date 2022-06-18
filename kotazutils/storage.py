
import shlex
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


def create_autoyaml(name, get_load=True, get_save=False, additional=None):
    def action(self, instance, value):
        if additional:
            additional(self, instance, value)
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
                yaml.dump(dict(auto.data.value), f, Dumper=Dumper)
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

##################



class StorageColumnAttribute:
    incompatabilities = []
    name = "ATTRIBUTE"
    
    
    def __init__(self, *args):
        self.args = args

    def compatability_check(self, attributes):
        for attribute in attributes:
            if attribute.name in self.incompatabilities:
                raise Exception("Incompatability between {} and {}".format(self.name, attribute.name))
            if attribute.name == self.name:
                raise Exception("Attribute {} already exists".format(self.name))
                

    def callback_universal(self, table, type, value):
        raise Exception("Not implemented (type: {})".format(type))

    def callback_int(self, table, value):
        self.callback_universal(table, "INTEGER", value)
    def callback_float(self, table, value):
        self.callback_universal(table, "FLOAT", value)
    def callback_str(self, table, value):
        self.callback_universal(table, "STR", value)
    def callback_bool(self, table, value):
        self.callback_universal(table, "BOOL", value)
    def callback_dict(self, table, value):
        self.callback_universal(table, "DICT", value)
    def callback_list(self, table, value):
        self.callback_universal(table, "LIST", value)
    def callback_set(self, table, value):
        self.callback_universal(table, "SET", value)
    def callback_uuid(self, table, value):
        self.callback_universal(table, "UUID", value)
    def callback_date(self, table, value):
        self.callback_universal(table, "DATE", value)
    def callback_timedelta(self, table, value):
        self.callback_universal(table, "TIMEDELTA", value)
    def callback_timestamp(self, table, value):
        self.callback_universal(table, "TIMESTAMP", value)
    def callback_blob(self, table, value):
        self.callback_universal(table, "BLOB", value)
    def callback_null(self, table, value):
        self.callback_universal(table, "NULL", value)
    def callback_any(self, table, value):
        self.callback_universal(table, "ANY", value)

class StorageColumn:
    def __init__(self, name, type, attributes):
        self.name = name
        self.type = type
        self.attributes = attributes
        
        # TYPES:   ✅❌    | INT   FLOAT    STR    BOOL  DICT     LIST    SET 
        # ATTRIBUTES:       |----------------------------------------------------
        # UNIQUE            | ❌     ❌     ❌     ❌     ❌     ❌     ❌ 
        # LIMIT (int) (int) | ❌     ❌     ❌     ❌     ❌     ❌     ❌ 
        # LINK (table name) | ❌     ❌     ❌     ❌     ❌     ❌     ❌ 
        # AUTOINCREMENT     | ❌     ❌     ❌     ❌     ❌     ❌     ❌ 
        # DEFAULT (value)   | ❌     ❌     ❌     ❌     ❌     ❌     ❌
        # REQUIRED          | ❌     ❌     ❌     ❌     ❌     ❌     ❌
        
        
        # TYPES:   ✅❌    | UUID  DATE  TIMEDELTA  TIMESTAMP  BLOB   NULL    ANY
        # ATTRIBUTES:       |-----------------------------------------------------
        # UNIQUE            | ❌     ❌     ❌         ❌     ❌     ❌     ❌ 
        # LIMIT (int) (int) | ❌     ❌     ❌         ❌     ❌     ❌     ❌ 
        # LINK (table name) | ❌     ❌     ❌         ❌     ❌     ❌     ❌ 
        # AUTOINCREMENT     | ❌     ❌     ❌         ❌     ❌     ❌     ❌ 
        # DEFAULT (value)   | ❌     ❌     ❌         ❌     ❌     ❌     ❌ 
        # REQUIRED          | ❌     ❌     ❌         ❌     ❌     ❌     ❌
 
        # ATTRUBUTE:        | UNIQUE LIMIT LINK AUTOINCREMENT DEFAULT REQUIRED
        # COMPATABILITY:    |--------------------------------------------------
        # UNIQUE            | 🟦     ❌     ❌     ❌         ❌     ❌
        # LIMIT (int) (int) | ❌     🟦     ❌     ❌         ❌     ❌
        # LINK (table name) | ❌     ❌     🟦     ❌         ❌     ❌
        # AUTOINCREMENT     | ❌     ❌     ❌     🟦         ❌     ❌
        # DEFAULT (value)   | ❌     ❌     ❌     ❌         🟦     ❌
        # REQUIRED          | ❌     ❌     ❌     ❌         ❌     🟦

    def process_insert(self, storage, table, value):
        callbacks = {
            "INT": lambda attr: attr.callback_int,
            "FLOAT": lambda attr: attr.callback_float,
            "STR": lambda attr: attr.callback_str,
            "BOOL": lambda attr: attr.callback_bool,
            "DICT": lambda attr: attr.callback_dict,
            "LIST": lambda attr: attr.callback_list,
            "SET": lambda attr: attr.callback_set,
            "UUID": lambda attr: attr.callback_uuid,
            "DATE": lambda attr: attr.callback_date,
            "TIMEDELTA": lambda attr: attr.callback_timedelta,
            "TIMESTAMP": lambda attr: attr.callback_timestamp,
            "BLOB": lambda attr: attr.callback_blob,
            "NULL": lambda attr: attr.callback_null,
            "ANY": lambda attr: attr.callback_any,
        }
        for attribute in self.attributes:
            attribute = storage.get_attribute(attribute)
            callbacks[self.type](attribute)(table, value)
        return value
            
    def serialize(self):
        return {
            "name": self.name,
            "type": self.type,
            "attributes": self.attributes,
        }
    
    @classmethod
    def deserialize(cls, data):
        return cls(data["name"], data["type"], data["attributes"])

class StorageColumns:
    def __init__(self, *columns):
        self.columns = columns if columns else []
    def add_column(self, column):
        self.columns.append(column)
    def get_columns(self):
        return self.columns
    
    def serialize(self):
        return [column.serialize() for column in self.columns]

    @classmethod
    def deserialize(cls, data):
        columns = []
        for column in data:
            columns.append(StorageColumn.deserialize(column))
        return cls(*columns)

class StorageTable:
    def __init__(self, storage, name):
        self.storage = storage
        self.name = name

        columns = self.storage.data[self.name]["__COLUMNS__"]
        print(columns)
        self.columns = StorageColumns().deserialize(columns)

    @property
    def data(self):
        return self.storage.data[self.name]["__DATA__"]


    def insert(self, **data):
        for column in self.columns.get_columns():
            if column.name not in data:
                raise Exception("Column '{}' is required. Use 'None' to skip".format(column.name))
        for key in data:
            if key not in [column.name for column in self.columns.get_columns()]:
                raise Exception("Column '{}' does not exist".format(key))
        payload = {}
        for column in self.columns.get_columns():
            column.process_insert(self.storage, self,  data[column.name])
            payload[column.name] = data[column.name]
        self.storage.data[self.name]["__DATA__"].append(payload)
        self.storage.save()
        print(self.storage.data)
        

class AttributeUnique(StorageColumnAttribute):
    incompatabilities = []
    name = "UNIQUE"

    def callback_universal(self, table, type, value):
        print(f'Таблица {table.name} получила значение {value} ({type}) для атрибута {self.name}. Аргументы: {self.args}')
class AttributeLimit(StorageColumnAttribute):
    incompatabilities = []
    name = "LIMIT"

    def callback_universal(self, table, type, value):
        print(f'Таблица {table.name} получила значение {value} ({type}) для атрибута {self.name}. Аргументы: {self.args}')

class StorageManager:
    def __init__(self, name, log=False):
        self.observer, self.load, self.save = create_autoyaml('t', get_save=True, additional=(lambda s, i, v: print('LOG:', v)) if log else None)
        self.name = name
        self.attributes = {}
        attributes = [AttributeUnique, AttributeLimit]

        for attribute in attributes:
            self.add_attribute(attribute)
    
    
    @property
    def data(self):
        return self.observer.data.value
    
    @data.setter
    def data(self, value):
        self.observer.data = value

    def add_attribute(self, attribute):
        self.attributes[attribute.name] = attribute

    def get_attribute(self, command):
        cmd = shlex.split(command)
        if cmd[0] not in self.attributes:
            raise Exception("Attribute '{}' does not exist".format(cmd[0]))
        return self.attributes[cmd[0]](*cmd[1:])
        
    def table_add(self, name, columns, force=True):
        if type(columns) is StorageColumns:
            pass
        elif type(columns) is list:
            columns = StorageColumns(*columns)
        else:
            raise TypeError("Columns must be list or StorageColumns")
    
        if self.table_exists(self.name) and not force:
            raise Exception("Table already exists")
        else:
            self.observer.data.update(
                {
                    name: {
                        "__COLUMNS__": columns.serialize(),
                        "__DATA__": [],
                    }
                }
            )
            return StorageTable(self, name)

    def table_exists(self, name):
        return name in self.data

class SimpleStorage:
    def __init__(self, name, log=False):
        self.name = name
        self.data = {}
        self.load()
        
    
    def save(self):
        with open(self.name, "w") as f:
            f.write(yaml.dump(self.data, Dumper=Dumper))

    def load(self):
        try:    
            with open(self.name, "r") as f:
                self.data = yaml.load(f, Loader=Loader)
            return True
        except FileNotFoundError:
            self.save()
            self.load()
            return False
        
    def table_add(self, name, default, raise_exception=False):
        if self.table_exists(name):
            if raise_exception:
                raise Exception("Table already exists")
            else:
                return self.table_get(name)
        else:
            self.observer.data.update(
                {
                    name: {
                        "__DEFAULT__": default,
                        "__DATA__": [],

                    }
                }
            )
        
    def table_exists(self, name):
        return name in self.data
    
    def table_get(self, name):
        return self.data[name]

    def table_list(self):
        return self.data.keys()
    
    def table_remove(self, name):
        if self.table_exists(name):
            del self.data[name]
            self.save()
        else:
            raise Exception("Table does not exist")

    def table_rename(self, name, new_name):
        if self.table_exists(name):
            self.data[new_name] = self.data[name]
            del self.data[name]
            self.save()
        else:
            raise Exception("Table does not exist")

    def table_default_record(self, name):
        if self.table_exists(name):
            return self.data[name]["__DEFAULT__"]
        else:
            raise Exception("Table does not exist")

    def table_columns(self, name):
        if self.table_exists(name):
            return self.data[name]["__COLUMNS__"].keys()
        else:
            raise Exception("Table does not exist")
    def record_validate(self, name, use_default=True, **data):
        if self.table_exists(name):
            columns = self.table_columns(name)
            default = self.table_default_record(name)
            for column in columns:
                if column not in data:
                    if use_default:
                        data[column] = default[column]
                    else:
                        raise Exception("Column '{}' is required. Use 'None' to skip".format(column))
            for key in data:
                if key not in columns:
                    raise Exception("Column '{}' does not exist".format(key))
            return True
        else:
            raise Exception("Table does not exist")

    def record_add(self, name, **data):
        if not self.table_exists(name):
            raise Exception("Table does not exist")
        if self.record_validate(name, **data):
            self.data[name]["__DATA__"].append(data)
            self.save()
    
    def record_get_by_id(self, name, id):
        if not self.table_exists(name):
            raise Exception("Table does not exist")
        return self.data[name]["__DATA__"][id]

    def record_get(self, name, *where):
        """
        >>> record_get("test", ["field", "value"], ["field2", "value"])
        {"field": "value", "field2": "value", "other": "other"}
        """
        if not self.table_exists(name):
            raise Exception("Table does not exist")
        records = self.data[name]["__DATA__"]
        for i, record in enumerate(records):
            for field, value in where:
                if record[field] != value:
                    break
            else:
                return record
        return None
    
    def record_gets(self, name, *where):
        """
        >>> record_gets("test", ["field", "value"], ["field2", "value"])
        [{"field": "value", "field2": "value", "other": "other"}]
        """
        if not self.table_exists(name):
            raise Exception("Table does not exist")
        records = self.data[name]["__DATA__"]
        result = []
        for i, record in enumerate(records):
            for field, value in where:
                if record[field] != value:
                    break
            else:
                result.append(record)
        return result
    
    def record_get_id(self, name, *where):
        """
        >>> record_get_id("test", ["field", "value"], ["field2", "value"])
        0
        """
        if not self.table_exists(name):
            raise Exception("Table does not exist")
        records = self.data[name]["__DATA__"]
        for i, record in enumerate(records):
            for field, value in where:
                if record[field] != value:
                    break
            else:
                return i
        return None
    
    def record_remove(self, name, *where):
        if not self.table_exists(name):
            raise Exception("Table does not exist")
        records = self.data[name]["__DATA__"]
        for i, record in enumerate(records):
            for field, value in where:
                if record[field] != value:
                    break
            else:
                del records[i]
        self.save()
    
    def record_remove_by_id(self, name, id):
        if not self.table_exists(name):
            raise Exception("Table does not exist")
        del self.data[name]["__DATA__"][id]
        self.save()
    
    def record_removes(self, name, *where):
        if not self.table_exists(name):
            raise Exception("Table does not exist")
        records = self.data[name]["__DATA__"]
        while record := self.record_get(name, *where):
            self.record_remove(name, *where)
        self.save()
    
    def record_update(self, name, *where, **data):
        if not self.table_exists(name):
            raise Exception("Table does not exist")
        records = self.data[name]["__DATA__"]
        for i, record in enumerate(records):
            for field, value in where:
                if record[field] != value:
                    break
            else:
                for key, value in data.items():
                    record[key] = value
        self.save()
