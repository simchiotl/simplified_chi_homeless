from dataclasses import asdict, astuple, fields
from enum import EnumMeta, Enum
from inspect import isclass

__all__ = [
    'Registerable',
    'EnumExtension',
    'DataClassExtension'
]


class Registerable(type):
    """Registerable

    Any object can register a string as its identifier to a class with this meta class, \
    and be get by this class using the identifier.
    """

    def __new__(mcs, name, bases, dct):
        cls = super().__new__(mcs, name, bases, dct)
        # clear register for new class, because only its subclass can register to it
        if hasattr(cls, 'name'):
            cls.name = ""
        return cls

    def __init__(cls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cls.PROTOTYPES = {}

    def register(cls, name):
        """Decorator that register a class or a functions to a register.

        Args:
            name (str): The name assigned to the class or functions to store in the register

        Returns:
            function: The decorator
        """

        def _decorator(function):
            cls.PROTOTYPES[name] = function
            if not hasattr(function, 'name') or len(function.name) == 0:
                function.name = name
            else:
                names = set(function.name.split(', '))
                if name not in names:
                    function.name += ", %s" % name
            return function

        return _decorator

    def __getitem__(cls, identifier):
        """A class method template for each pluggable class

        Args:
            identifier (str or class): the identifier of this class's subclasses

        Returns:
            class: the exact subclass
        """
        if identifier is None:
            return None
        if isinstance(identifier, str) and identifier in cls.PROTOTYPES:
            return cls.PROTOTYPES[identifier]
        if isclass(identifier) and issubclass(identifier, cls):
            return identifier
        if callable(identifier) and hasattr(identifier, 'name') and identifier.name in cls.PROTOTYPES:
            return identifier
        raise ValueError(
            'Could not interpret the identifier: {}'.format(identifier))


class _EnumExtensionMeta(EnumMeta):
    """Can tell if a str is valid member name"""

    def __contains__(cls, item):
        if isinstance(item, str):
            return item in cls._member_map_
        return super().__contains__(item)

    def get(cls, item, default=None):
        if item in cls:
            return cls[item]
        return default


class EnumExtension(Enum, metaclass=_EnumExtensionMeta):
    pass


class DataClassExtension:
    """Add some static libraries of ``dataclasses`` as class methods"""

    def _asdict(self):
        return asdict(self)

    def _astuple(self):
        return astuple(self)

    @property
    def _fields(self):
        return fields(self)

    def __dict__(self):
        return self._asdict()

    def __str__(self):
        return str(self.__dict__())
