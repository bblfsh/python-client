from bblfsh.aliases import ParseResponse
from bblfsh.node import Node
from bblfsh.node_iterator import NodeIterator
from bblfsh.pyuast import decode, iterator, uast
from bblfsh.tree_order import TreeOrder


class ResponseError(Exception):
    pass


class NotNodeIterationException(Exception):
    pass


class GetOnEmptyNodeException(Exception):
    pass


class ResultContext:
    def __init__(self, grpc_response: ParseResponse = None) -> None:
        if grpc_response:
            if grpc_response.errors:
                raise ResponseError("\n".join(
                    [error.text for error in grpc_response.errors])
                )
            self._response = grpc_response
            self.ctx = decode(grpc_response.uast, format=0)
        else:
            self._response = None
            self.ctx = uast()

    def filter(self, query: str) -> NodeIterator:
        return NodeIterator(self.ctx.filter(query), self.ctx)

    def get_all(self) -> dict:
        return self.ctx.load()

    def iterate(self, order: int) -> NodeIterator:
        TreeOrder.check_order(order)
        return NodeIterator(iterator(self.ctx.root(), order), self.ctx)

    # Encode in binary format by default
    def encode(self, node: dict = None, fmt: int = 0):
        encoded = self.ctx.encode(node, fmt)
        return encoded

    @property
    def language(self) -> str:
        return self._response.language

    @property
    def filename(self) -> str:
        return self._response.filename

    @property
    def root(self) -> Node:
        return Node(node_ext=self.ctx.root(), ctx=self.ctx)

    @property
    def uast(self) -> Node:
        return self.root

    @property
    def ast(self) -> Node:
        return self.root

    def __str__(self) -> str:
        return str(self.get_all())

    def __repr__(self) -> str:
        return repr(self.get_all())


# Python context
class Context:
    def __init__(self, root: dict) -> None:
        self.ctx = uast()
        self.root = root

    def filter(self, query: str) -> dict:
        return self.ctx.filter(query, self.root)

    def iterate(self, order: int) -> iterator:
        TreeOrder.check_order(order)
        return iterator(self.root, order)

    def encode(self, fmt: int = 0):
        encoded = self.ctx.encode(self.root, fmt)
        return encoded


def context(root: dict) -> Context:
    return Context(root)
