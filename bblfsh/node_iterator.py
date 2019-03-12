from typing import Union, Optional

from bblfsh.node import Node
from bblfsh.result_context import ResultMultiType
from bblfsh.pyuast import Context, IteratorExt, NodeExt, iterator
from bblfsh.tree_order import TreeOrder


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


