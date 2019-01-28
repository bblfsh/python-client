import copy
import typing as t
from collections import MutableSequence

from bblfsh.aliases import ParseResponse
from bblfsh.pyuast import Context, IteratorExt, NodeExt, decode, iterator, uast
from bblfsh.tree_order import TreeOrder


class ResponseError(Exception):
    pass


class ResultTypeException(Exception):
    pass


class NotNodeIterationException(Exception):
    pass


class GetOnEmptyNodeException(Exception):
    pass


ResultMultiType = t.Union[dict, int, float, bool, str, None]


class CompatPosition:
    """
    v1 positions were extracted as node.[start|end]_position.[line|col|offset]. To
    emulate that, this dictionary will be returned when accesing the old position
    properties and its setters will update the parent Node real position ones.
    """

    def __init__(self, parent_pos: dict):
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
    def __init__(self, parent: "Node"):
        self._children = parent.get_dict()["@children"]

    @staticmethod
    def _node2dict(n):
        if isinstance(n, Node):
            # Convert to dict before appending
            return n.get_dict()
        return n

    def __len__(self):
        return len(self._children)

    def __getitem__(self, idx):
        return self._children[idx]

    def __delitem__(self, idx):
        del self._children[idx]

    def __setitem__(self, idx, val):
        self._children[idx] = self._node2dict(val)

    def insert(self, idx, val):
        self._children.insert(idx, self._node2dict(val))

    def append(self, val):
        self._children.append(self._node2dict(val))

    def extend(self, items) -> None:
        for i in items:
            self.append(i)

    def __str__(self):
        return str(self._children)

EMPTY_NODE_DICT = {
    "@type": "",
    "@token": "",
    "@role": [],
    "@children": [],
}

# XXX check if I can totally remove ctx from this
class Node:
    def __init__(self, node_ext: NodeExt = None, value: ResultMultiType=None,
                 ctx: Context = None) -> None:

        if node_ext and (value is not None):
            # XXX exception type
            raise Exception(
                "Node creation can have node_ext or value, not both"
            )

        self._node_ext = node_ext
        if node_ext is None:
            self._internal_node = value if (value is not None)\
                else copy.deepcopy(EMPTY_NODE_DICT)
        elif not isinstance(node_ext, NodeExt):
            # XXX exception type
            raise Exception("Node instanced with a non NodeExt first argument: %s"
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

    def _get_typed(self, *type_list: t.List[type]) -> ResultMultiType:
        self._ensure_load()

        if type(self._internal_node) not in type_list:
            raise ResultTypeException("Expected {} result, but type is '{}'"
                                      .format(str(type_list), type(self._internal_node)))
        return self._internal_node

    def get_bool(self) -> bool:
        return t.cast(bool, self._get_typed(bool))

    def get_float(self) -> float:
        res: ResultMultiType = self._get_typed(float, int)
        if isinstance(res, int):
            res = float(res)
        return t.cast(float, res)

    def get_int(self) -> int:
        return t.cast(int, self._get_typed(int))

    def get_str(self) -> str:
        return t.cast(str, self._get_typed(str))

    def get_dict(self) -> dict:
        return t.cast(dict, self._get_typed(dict))

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
    def properties(self):
        return self.get_dict()

    def _is_dict_list(self, key: str) -> t.Optional[t.List]:
        val = self.get_dict().get(key, None)
        if not val or not isinstance(val, t.List):
            return None

        for i in val:
            if not isinstance(i, dict):
                return None

        return val

    @property
    def children(self):
        return CompatChildren(self)

    @property
    def token(self) -> str:
        return self.get_dict()["@token"]

    @token.setter
    def token(self, t: str) -> None:
        d = self.get_dict()
        d["@token"] = t

    @property
    def roles(self) -> t.List:
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
    def start_position(self):
        self._add_position()
        start = self.get_dict()["@pos"]["start"]
        return CompatPosition(start)

    @property
    def end_position(self):
        self._add_position()
        end = self.get_dict()["@pos"]["end"]
        return CompatPosition(end)


# XXX remove ctx if removed from Node
class NodeIterator:
    def __init__(self, iter_ext: IteratorExt, ctx: Context) -> None:
        self._iter_ext = iter_ext
        self._ctx = ctx
        # default, can be changed on self.iterate()
        self._order: TreeOrder = TreeOrder.PRE_ORDER
        # saves the last node for re-iteration with iterate()
        self._last_node: Node = None

    def __iter__(self) -> 'NodeIterator':
        return self

    def __next__(self) -> t.Union[ResultMultiType, Node]:
        next_node = next(self._iter_ext)

        if isinstance(next_node, NodeExt):
            # save last node for potential re-iteration
            self._last_node = Node(node_ext=next_node, ctx=self._ctx)
            return self._last_node
        # non node (bool, str, etc)
        return next_node

    def iterate(self, order: int) -> 'NodeIterator':
        if self._last_node is None:
            self._last_node = Node(node_ext=next(self._iter_ext),
                                   ctx=self._ctx)

        TreeOrder.check_order(order)
        self._order = order
        return NodeIterator(
            iterator((self._last_node._node_ext), order), self._ctx)


class ResultContext:
    def __init__(self, grpc_response: ParseResponse = None) -> None:
        if grpc_response:
            if grpc_response.errors:
                raise ResponseError("\n".join(
                    [error.text for error in grpc_response.errors])
                )
            self._response = grpc_response
            self._ctx = decode(grpc_response.uast, format=0)
        else:
            self._response = None
            self._ctx = uast()

    def filter(self, query: str) -> NodeIterator:
        return NodeIterator(self._ctx.filter(query), self._ctx)

    def get_all(self) -> dict:
        return self._ctx.load()

    def iterate(self, order: int) -> NodeIterator:
        TreeOrder.check_order(order)
        return NodeIterator(iterator(self._ctx.root(), order), self._ctx)

    @property
    def language(self) -> str:
        return self._response.language

    @property
    def filename(self) -> str:
        return self._response.filename

    @property
    def uast(self) -> Node:
        return Node(node_ext=self._ctx.root(), ctx=self._ctx)

    @property
    def ast(self) -> Node:
        return Node(node_ext=self._ctx.root(), ctx=self._ctx)

    def __str__(self) -> str:
        return str(self.get_all())

    def __repr__(self) -> str:
        return repr(self.get_all())
