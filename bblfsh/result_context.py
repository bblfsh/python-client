from typing import Union, Optional

from bblfsh.aliases import ParseResponse
from bblfsh.node import Node
from bblfsh.pyuast import Context, IteratorExt, NodeExt, decode, iterator, uast
from bblfsh.tree_order import TreeOrder


class ResponseError(Exception):
    pass


class NotNodeIterationException(Exception):
    pass


class GetOnEmptyNodeException(Exception):
    pass


ResultMultiType = Union[dict, int, float, bool, str, None]


# XXX remove ctx if removed from Node
class NodeIterator:
    def __init__(self, iter_ext: IteratorExt, ctx: Context) -> None:
        self._iter_ext = iter_ext
        self._ctx = ctx
        # default, can be changed on self.iterate()
        self._order: TreeOrder = TreeOrder.PRE_ORDER
        # saves the last node for re-iteration with iterate()
        self._last_node: Optional[Node] = None

    def __iter__(self) -> 'NodeIterator':
        return self

    def __next__(self) -> Union[ResultMultiType, Node]:
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
