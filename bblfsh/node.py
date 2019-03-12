import copy
from collections import MutableSequence
from typing import Union, List, cast, Optional, Any

from bblfsh.pyuast import Context, NodeExt, uast
from bblfsh.result_context import ResultMultiType

class ResultTypeException(Exception):
    pass

class CompatPosition:
    """
    v1 positions were extracted as node.[start|end]_position.[line|col|offset]. To
    emulate that, this dictionary will be returned when accesing the old position
    properties and its setters will update the parent Node real position ones.
    """

    def __init__(self, parent_pos: dict) -> None:
        self._parent_pos = parent_pos

    @property
    def line(self) -> int:
        return self._parent_pos["line"]

    @line.setter
    def line(self, v: int) -> None:
        self._parent_pos["line"] = v

    @property
    def col(self) -> int:
        return self._parent_pos["col"]

    @col.setter
    def col(self, v: int) -> None:
        self._parent_pos["col"] = v

    @property
    def offset(self) -> int:
        return self._parent_pos["offset"]

    @offset.setter
    def offset(self, v: int) -> None:
        self._parent_pos["offset"] = v


class CompatChildren(MutableSequence):
    def __init__(self, parent: "Node") -> None:
        self._children = parent.get_dict()["@children"]

    @staticmethod
    def _node2dict(n: Union['Node', dict]) -> dict:
        if isinstance(n, Node):
            # Convert to dict before appending
            return n.get_dict()
        return n

    def __len__(self) -> int:
        return len(self._children)

    def __getitem__(self, idx: Union[int, slice]) -> Any:
        return self._children[idx]

    def __delitem__(self, idx: Union[int, slice]) -> None:
        del self._children[idx]

    def __setitem__(self, idx: Union[int, slice], val: Union['Node', dict]) -> None:
        self._children[idx] = self._node2dict(val)

    def insert(self, idx: int, val: Union['Node', dict]) -> None:
        self._children.insert(idx, self._node2dict(val))

    def append(self, val: Union['Node', dict]) -> None:
        self._children.append(self._node2dict(val))

    def extend(self, items: List[Union['Node', dict]]) -> None:
        for i in items:
            self.append(i)

    def __str__(self) -> str:
        return str(self._children)

EMPTY_NODE_DICT = {
    "@type": "",
    "@token": "",
    "@role": [],
    "@children": [],
}

class NodeInstancingException(Exception):
    pass

# XXX check if I can totally remove ctx from this
class Node:
    def __init__(self, node_ext: NodeExt = None, value: ResultMultiType=None,
                 ctx: Context = None) -> None:

        if node_ext and (value is not None):
            raise NodeInstancingException("Node creation can have node_ext or value, not both")

        self._node_ext = node_ext
        if node_ext is None:
            self._internal_node = value if (value is not None) \
                else copy.deepcopy(EMPTY_NODE_DICT)
        elif not isinstance(node_ext, NodeExt):
            raise NodeInstancingException("Node instanced with a non NodeExt first argument: %s"
                                          % str(type(node_ext)))
        else:
            # generate self._internal_node from the NodeExt
            self._ensure_load()

        if isinstance(self._internal_node, dict):
            self._load_children()

        self._ctx = ctx if ctx is not None else uast()

    def _load_children(self) -> None:
        "Get all properties of type node or dict and load them into the list"
        d = self.get_dict()
        children = d["@children"]
        for k, v in d.items():
            if k in ["@children", "@pos"]:
                continue
            if type(v) in [Node, dict]:
                children.append(v)

    def _ensure_load(self) -> None:
        if self._node_ext is not None:
            self._internal_node = self._node_ext.load()
        if isinstance(self._internal_node, dict):
            self._internal_node["@children"] = self._internal_node.get("@children", [])

    def __str__(self) -> str:
        return str(self.get())

    def __repr__(self) -> str:
        return repr(self.get())

    def get(self) -> ResultMultiType:
        self._ensure_load()
        return self._internal_node

    def _get_typed(self, *type_list: type) -> ResultMultiType:
        self._ensure_load()

        if type(self._internal_node) not in type_list:
            raise ResultTypeException("Expected {} result, but type is '{}'"
                                      .format(str(type_list), type(self._internal_node)))
        return self._internal_node

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

    # TODO(juanjux): backward compatibility methods, remove once v1
    #  is definitely deprecated

    @property
    def internal_type(self) -> str:
        return self.get_dict()["@type"]

    @internal_type.setter
    def internal_type(self, t: str) -> None:
        d = self.get_dict()
        d["@type"] = t

    @property
    def properties(self) -> dict:
        return self.get_dict()

    def _is_dict_list(self, key: str) -> Optional[List]:
        val = self.get_dict().get(key, None)
        if not val or not isinstance(val, List):
            return None

        for i in val:
            if not isinstance(i, dict):
                return None

        return val

    @property
    def children(self) -> CompatChildren:
        return CompatChildren(self)

    @property
    def token(self) -> str:
        return self.get_dict()["@token"]

    @token.setter
    def token(self, t: str) -> None:
        d = self.get_dict()
        d["@token"] = t

    @property
    def roles(self) -> List:
        return self.get_dict().get("@role", [])

    def _add_position(self) -> None:
        d = self.get_dict()
        if "@pos" not in d:
            d["@pos"] = {
                "@type": "uast:Positions",
                "start": {
                    "@type": "uast:Position",
                    "offset": -1,
                    "line": -1,
                    "col": -1,
                },
                "end": {
                    "@type": "uast:Position",
                    "offset": -1,
                    "line": -1,
                    "col": -1,
                }
            }

    @property
    def start_position(self) -> CompatPosition:
        self._add_position()
        start = self.get_dict()["@pos"]["start"]
        return CompatPosition(start)

    @property
    def end_position(self) -> CompatPosition:
        self._add_position()
        end = self.get_dict()["@pos"]["end"]
        return CompatPosition(end)


