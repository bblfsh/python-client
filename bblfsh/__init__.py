from bblfsh.client import BblfshClient
from bblfsh.pyuast import filter, filter_bool, filter_number, filter_string, iterator
from bblfsh.aliases import *

class TreeOrder:
    PRE_ORDER      = 0
    POST_ORDER     = 1
    LEVEL_ORDER    = 2
    POSITION_ORDER = 3

# "in" is a reserved keyword in Python thus can't be used as package name, so
# we import by string

class RoleSearchException(Exception):
    pass


def role_id(role_name: str) -> int:
    try:
        name = DESCRIPTOR.enum_types_by_name["Role"].values_by_name[role_name].number
    except KeyError:
        raise RoleSearchException("Role with name '{}' not found".format(role_name))

    return name


def role_name(role_id: int) -> str:
    try:
        id_ = DESCRIPTOR.enum_types_by_name["Role"].values_by_number[role_id].name
    except KeyError:
        raise RoleSearchException("Role with ID '{}' not found".format(role_id))

    return id_
