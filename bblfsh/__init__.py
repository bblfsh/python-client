from bblfsh.client import BblfshClient
from bblfsh.pyuast import decode, iterator, uast
from bblfsh.tree_order import TreeOrder
from bblfsh.aliases import *


class RoleSearchException(Exception):
    pass


def role_id(rname: str) -> int:
    try:
        name = DESCRIPTOR.enum_types_by_name["Role"].values_by_name[rname].number
    except KeyError:
        raise RoleSearchException("Role with name '{}' not found".format(rname))

    return name


def role_name(rid: int) -> str:
    try:
        id_ = DESCRIPTOR.enum_types_by_name["Role"].values_by_number[rid].name
    except KeyError:
        raise RoleSearchException("Role with ID '{}' not found".format(rid))

    return id_
