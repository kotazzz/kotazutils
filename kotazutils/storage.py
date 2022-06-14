import sqlite3
from contextlib import contextmanager
import yaml
import ujson
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


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
        self.kwargs.update({
            'callback': callback,
        })

        self._value = None

        self._instance_to_name_mapping = {}
        self._instance = None

        self._parent_observer = None

        self._value_parent = None
        self._value_index = None

    @property
    def value(self):
        """Returns the content of attached data.
        """
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
        """Divulges that data content has been change calling callback.
        """
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
                    ['append', 'extend', 'insert', 'remove', 'pop', 'sort', 'reverse'] + # list methods
                    ['clear', 'pop', 'update']                                           # dict methods
        ):
            return observe(self, attr)
        return attr


class AutoJson:
    def __init__(self, name):
        self.name = name
        self.data = Observer({}, self.on_change)
        self.observe = True
        

    @contextmanager
    def disabled_observe(self):
        self.observe = False
        yield
        self.observe = True

    def on_change(self):
        with open(self.name, 'w') as f:
            ujson.dump(self.data.value, f)

    def load(self):
        with self.disabled_observe():
            with open(self.name, 'r') as f:
                self.data.value = ujson.load(f)
    
    def save(self):
        with open(self.name, 'w') as f:
            ujson.dump(self.data.value, f)

class AutoYaml:
    def __init__(self, name):
        self.name = name
        self.data = Observer({}, self.on_change)
        self.observe = True

    @contextmanager
    def disabled_observe(self):
        self.observe = False
        yield
        self.observe = True

    def on_change(self):
        with open(self.name, 'w') as f:
            yaml.dump(self.data.value, f)

    def load(self):
        try:
            with self.disabled_observe():
                with open(self.name, 'r') as f:
                    self.data.value = yaml.load(f)
        except FileNotFoundError:
            self.save()
            self.load()

    def save(self):
        with open(self.name, 'w') as f:
            yaml.dump(self.data.value, f)
