from bblfsh.aliases import ParseResponse
from bblfsh.pyuast import decode, iterator, uast
from bblfsh.tree_order import TreeOrder

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

    def encode(self, fmt: int):
        encoded = self.ctx.encode(self.root, fmt)
        return encoded

def context(root: dict) -> Context:
    return Context(root)
