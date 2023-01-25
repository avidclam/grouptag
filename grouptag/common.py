from collections.abc import Mapping, MutableSequence
from numbers import Number


def is_list(x):
    # Tuple goes as list here, can be used interchangeably for rule readability.
    # However, mind that tuples are not json-serializable.
    return isinstance(x, (MutableSequence, tuple))


def is_dict(x):
    return isinstance(x, Mapping)


def is_numeric(x):
    return isinstance(x, Number) and not isinstance(x, bool)


def is_and_logic(level):
    # Level of nesting of the group pattern-action specifier
    # defines whether pattern masks are grouped with AND logic.
    return not level % 2
