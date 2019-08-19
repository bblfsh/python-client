import copy
from collections import MutableSequence
from typing import Union, List, cast, Optional, Any

from bblfsh.pyuast import Context, NodeExt, IteratorExt, iterator

from bblfsh.roles import role_id
from bblfsh.tree_order import TreeOrder
from bblfsh.type_aliases import ResultMultiType


class Position:
    def __init__(self, pos: dict) -> None:
        self._pos = pos

    @property
    def line(self) -> int:
        return self._pos["line"]

    @line.setter
    def line(self, v: int) -> None:
        self._pos["line"] = v

    @property
    def col(self) -> int:
        return self._pos["col"]

    @col.setter
    def col(self, v: int) -> None:
        self._pos["col"] = v

    @property
    def offset(self) -> int:
        return self._pos["offset"]

    @offset.setter
    def offset(self, v: int) -> None:
        self._pos["offset"] = v

    @property
    def type(self) -> str:
        return "uast:Position"


class NodePosition:
    def __init__(self, **kwargs) -> None:
        for key, value in kwargs.items():
            self.__dict__[key] = value

    def __len__(self):
        return len(self.__dict__)

    def __getitem__(self, key):
        return self.__dict__.get(key, None)

    def __setitem__(self, key, item):
        self.__dict__[key] = item

    def __contains__(self, item):
        return item in self.__dict__

    def __iter__(self):
        return iter(self.__dict__)

    @property
    def type(self) -> str:
        return "uast:Positions"


class NodeTypedGetException(Exception):
    pass

class NodeInstancingException(Exception):
    pass

EMPTY_NODE_DICT = {
    "@type": "",
    "@token": "",
    "@role": [],
    "@children": [],
}

class Node:
    def __init__(self, node_ext: NodeExt = None, ctx: Context = None, value: ResultMultiType = None) -> None:

        if node_ext and (value is not None):
            raise NodeInstancingException("Node creation can have node_ext or value, not both")

        if node_ext is None:
            self.internal_node = value if (value is not None) \
                else copy.deepcopy(EMPTY_NODE_DICT)
        elif not isinstance(node_ext, NodeExt):
            raise NodeInstancingException("Node instanced with a non NodeExt first argument: %s"
                                          % str(type(node_ext)))
        else:
            # generate self.internal_node from the NodeExt
            self.internal_node = node_ext.load()

        self.ctx = ctx
        self.node_ext = node_ext

    def __str__(self) -> str:
        return str(self.get())

    def __repr__(self) -> str:
        return repr(self.get())

    def get(self) -> ResultMultiType:
        return self.internal_node

    def _get_typed(self, *type_list: type) -> ResultMultiType:
        if type(self.internal_node) not in type_list:
            raise NodeTypedGetException("Expected {} result, but type is '{}'"
                                        .format(str(type_list), type(self.internal_node)))
        return self.internal_node

    def get_bool(self) -> bool:
        return cast(bool, self._get_typed(bool))

    def get_float(self) -> float:
        res: ResultMultiType = self._get_typed(float, int)
        if isinstance(res, int):
            res = float(res)
        return cast(float, res)

    def get_int(self) -> int:
        return cast(int, self._get_typed(int))

    def get_str(self) -> str:
        return cast(str, self._get_typed(str))

    def get_dict(self) -> dict:
        return cast(dict, self._get_typed(dict))

    def _iterator(self, it: IteratorExt) -> 'NodeIterator':
        import bblfsh.node_iterator
        return bblfsh.node_iterator.NodeIterator(it, self.ctx)

    def iterate(self, order: int) -> 'NodeIterator':
        TreeOrder.check_order(order)
        return self._iterator(iterator(self.node_ext, order))

    def filter(self, query: str) -> 'NodeIterator':
        return self._iterator(self.ctx.filter(query, self.node_ext))

    @property
    def properties(self) -> dict:
        return self.get_dict()

    @property
    def type(self) -> str:
        return self.get_dict()["@type"]

    @type.setter
    def type(self, t: str) -> None:
        d = self.get_dict()
        d["@type"] = t

    @property
    def children(self) -> List["Node"]:
        d = self.get_dict()

        if "_children" not in d:
            d["_children"] = []

        children = d["_children"]
        for k, v in d.items():
            if k in ("_children", "@pos", "@role", "@type"):
                continue

            tv = type(v)
            if tv in (Node, dict):
                if v not in children:
                    children.append(v)
            elif tv in (list, tuple):
                # Get all node|dict types inside the list and add to children
                children.extend([i for i in v if type(i) in (Node, dict) and i not in children])

        return children

    @property
    def token(self) -> str:
        return self.get_dict().get("@token", "")

    @token.setter
    def token(self, t: str) -> None:
        d = self.get_dict()
        d["@token"] = t

    @property
    def roles(self) -> List:
        return [role_id(name) for name in self.get_dict().get("@role", [])]

    @property
    def position(self) -> NodePosition:
        pos = NodePosition()

        d = self.get_dict()
        if "@pos" not in d:
            return pos

        for key, value in d["@pos"].items():
            if key == "@type":
                continue
            pos[key] = Position(value)

        return pos
