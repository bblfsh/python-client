import copy
from collections import MutableSequence
from typing import Union, List, cast, Optional, Any

from bblfsh.pyuast import Context, NodeExt, IteratorExt, iterator

from bblfsh.roles import role_id
from bblfsh.tree_order import TreeOrder
from bblfsh.type_aliases import ResultMultiType


class NodeTypedGetException(Exception):
    pass


class CompatPosition:
    """
    v1 positions were extracted as node.[start|end]_position.[line|col|offset]. To
    emulate that, this dictionary will be returned when accessing the old position
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

# This is for v1 "node.children" compatibility. It will update the children
# property with the dict or Node objects in properties or list/tuple properties
# when .children is accessed (because the user could change the node using get_dict()
# or .properties).
# Also, all these " in children" are O(n) so this will be slow for frequently accessing
# the children property on big nodes.
class CompatChildren(MutableSequence):
    def __init__(self, parent: "Node") -> None:
        self._par_dict = parent.get_dict()
        self._children = self._sync_children()

    def _sync_children(self) -> List["Node"]:
        if "_children" not in self._par_dict:
            self._par_dict["_children"] = []
        children = self._par_dict["_children"]
        for k, v in self._par_dict.items():
            if k in ("_children", "@pos", "@role", "@type"):
                continue

            tv = type(v)
            if tv in (Node, dict):
                if v not in children:
                    children.append(v)
            elif tv in (list, tuple):
                # Get all node|dict types inside the list and add to children
                children.extend([i for i in v if type(i) in (Node, dict) and i not in children])
            # else ignore it
        return children

    @staticmethod
    def _node2dict(n: Union['Node', dict]) -> dict:
        if isinstance(n, Node):
            # Convert to dict before appending
            return n.get_dict()
        return n

    def __len__(self) -> int:
        return len(self._children)

    def __getitem__(self, idx: Union[int, slice]) -> Any:
        return Node(value=self._children[idx])

    def __delitem__(self, idx: Union[int, slice]) -> None:
        del self._children[idx]

    def __setitem__(self, idx: Union[int, slice], val: Union['Node', dict]) -> None:
        self._par_dict["_children"].__setitem__(idx, self._node2dict(val))
        self._children = self._sync_children()

    def insert(self, idx: int, val: Union['Node', dict]) -> None:
        self._par_dict["_children"].insert(idx, self._node2dict(val))
        self._children = self._sync_children()

    def append(self, val: Union['Node', dict]) -> None:
        self._par_dict["_children"].append(self._node2dict(val))
        self._children = self._sync_children()

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
        # TODO: this avoids circular imports; any better way to make it work?
        import bblfsh.node_iterator
        return bblfsh.node_iterator.NodeIterator(it, self.ctx)

    def iterate(self, order: int) -> 'NodeIterator':
        TreeOrder.check_order(order)
        return self._iterator(iterator(self.node_ext, order))

    def filter(self, query: str) -> 'NodeIterator':
        return self._iterator(self.ctx.filter(query, self.node_ext))

    # TODO(juanjux): backward compatibility methods, remove once v1
    #                is definitely deprecated

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
    def children(self) -> List["Node"]:
        return CompatChildren(self)

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

    def _add_position(self) -> None:
        d = self.get_dict()
        if "@pos" not in d:
            d["@pos"] = {
                "@type": "uast:Positions",
                "start": Node._get_default_position(),
                "end": Node._get_default_position()
            }

    @property
    def start_position(self) -> CompatPosition:
        self._add_position()
        start = self.get_dict()["@pos"].get("start", Node._get_default_position())
        return CompatPosition(start)

    @property
    def end_position(self) -> CompatPosition:
        self._add_position()
        end = self.get_dict()["@pos"].get("end", Node._get_default_position())
        return CompatPosition(end)

    @staticmethod
    def _get_default_position():
        return {
            "@type": "uast:Position",
            "offset": 0,
            "line": 0,
            "col": 0,
        }
