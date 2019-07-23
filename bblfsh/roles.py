from bblfsh.aliases import DESCRIPTOR


class RoleSearchException(Exception):
    pass


def role_id(rname: str) -> int:
    try:
        name = DESCRIPTOR.enum_types_by_name["Role"].values_by_name[rname.upper()].number
    except KeyError:
        raise RoleSearchException("Role with name '{}' not found".format(rname))

    return name


def role_name(rid: int) -> str:
    try:
        id_ = DESCRIPTOR.enum_types_by_name["Role"].values_by_number[rid].name
    except KeyError:
        raise RoleSearchException("Role with ID '{}' not found".format(rid))

    return id_.upper()
