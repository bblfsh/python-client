from typing import Union, Optional

from bblfsh.node import Node
from bblfsh.pyuast import Context, IteratorExt, NodeExt, iterator
from bblfsh.tree_order import TreeOrder
from bblfsh.type_aliases import ResultMultiType


class NodeIterator:
    # ctx is not used but prevents the context from deallocating (bug). This is because
    # currently the IteratorExt will go away if the context from which it was
    # called does.
    def __init__(self, iter_ext: IteratorExt, ctx: Context = None) -> None:
        self._iter_ext = iter_ext
        # default, can be changed on self.iterate()
        self._order: TreeOrder = TreeOrder.PRE_ORDER
        # saves the last node for re-iteration with iterate()
        self._last_node: Optional[Node] = None
        self.ctx = ctx

    def __iter__(self) -> 'NodeIterator':
        return self

    def __next__(self) -> Union[ResultMultiType, Node]:
        next_node = next(self._iter_ext)

        if isinstance(next_node, NodeExt):
            # save last node for potential re-iteration
            self._last_node = Node(node_ext=next_node)
            return self._last_node
        # non node (bool, str, etc)
        return next_node

    def iterate(self, order: int) -> 'NodeIterator':
        if self._last_node is None:
            self._last_node = Node(node_ext=next(self._iter_ext))

        TreeOrder.check_order(order)
        self._order = order
        return NodeIterator(iterator((self._last_node.node_ext), order), self.ctx)
