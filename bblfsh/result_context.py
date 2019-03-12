import typing as t

from bblfsh.aliases import ParseResponse
from bblfsh.pyuast import decode, IteratorExt, NodeExt, iterator
from bblfsh.tree_order import TreeOrder


class ResponseError(Exception):
    pass


class ResultTypeException(Exception):
    pass


class NotNodeIterationException(Exception):
    pass


# ResultMultiType = t.NewType("ResultMultiType", t.Union[dict, int, float, bool, str])
ResultMultiType = t.Union[dict, int, float, bool, str, None]


class Node:
    def __init__(self, node_ext: NodeExt) -> None:
        self._node_ext = node_ext
        self._loaded_node: ResultMultiType = None

    def _ensure_load(self) -> None:
        if self._loaded_node is None:
            self._loaded_node = self._node_ext.load()

    def __str__(self) -> str:
        return str(self.get())

    def __repr__(self) -> str:
        return repr(self.get())

    def get(self) -> ResultMultiType:
        self._ensure_load()
        return self._loaded_node

    def _get_typed(self, type_: t.Union[type, t.List[type]]) -> ResultMultiType:
        self._ensure_load()

        if not isinstance(type_, list) and not isinstance(type_, tuple):
            type_list = [type_]
        else:
            type_list = type_

        if type(self._loaded_node) not in type_list:
            raise ResultTypeException("Expected {} result, but type is '{}'"
                                      .format(str(type_list), type(self._loaded_node)))
        return self._loaded_node

    def get_bool(self) -> bool:
        return t.cast(bool, self._get_typed(bool))

    def get_float(self) -> float:
        res: ResultMultiType = self._get_typed([float, int])
        if isinstance(res, int):
            res = float(res)
        return t.cast(float, res)

    def get_int(self) -> int:
        return t.cast(int, self._get_typed(int))

    def get_str(self) -> str:
        return t.cast(str, self._get_typed(str))

    def get_dict(self) -> dict:
        return t.cast(dict, self._get_typed(dict))

    def iterate(self, order: int) -> 'NodeIterator':
        if not isinstance(self._node_ext, NodeExt):
            raise NotNodeIterationException("Cannot iterate over leaf of type '{}'"
                                            .format(type(self._node_ext)))
        TreeOrder.check_order(order)
        return NodeIterator(iterator(self._node_ext, order))


class NodeIterator:
    def __init__(self, iter_ext: IteratorExt) -> None:
        self._iter_ext = iter_ext

    def __iter__(self) -> 'NodeIterator':
        return self

    def __next__(self) -> Node:
        return Node(next(self._iter_ext))

    def iterate(self, order: int) -> 'NodeIterator':
        TreeOrder.check_order(order)
        return NodeIterator(iterator(next(self._iter_ext), order))


class ResultContext:
    def __init__(self, grpc_response: ParseResponse) -> None:
        if grpc_response.errors:
            raise ResponseError("\n".join(
                [error.text for error in grpc_response.errors])
            )

        self._response = grpc_response
        self._ctx = decode(grpc_response.uast, format=0)

    def filter(self, query: str) -> NodeIterator:
        return NodeIterator(self._ctx.filter(query))

    def get_all(self) -> dict:
        return self._ctx.load()

    def iterate(self, order: int) -> NodeIterator:
        TreeOrder.check_order(order)
        return NodeIterator(iterator(self._ctx.root(), order))

    @property
    def language(self) -> str:
        return self._response.language

    @property
    def uast(self) -> t.Any:
        return self._response.uast

    def __str__(self) -> str:
        return str(self.get_all())

    def __repr__(self) -> str:
        return repr(self.get_all())
