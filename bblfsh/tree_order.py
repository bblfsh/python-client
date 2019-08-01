from enum import IntEnum
from bblfsh.pyuast import TreeOrder

class TreeOrder(IntEnum):
    # Gives no assurances over the iteration order of the tree
    # Uses the fastest one available (the one that the tree
    # natively supports)
    ANY_ORDER      = TreeOrder.ANY_ORDER()
    PRE_ORDER      = TreeOrder.PRE_ORDER()
    POST_ORDER     = TreeOrder.POST_ORDER()
    LEVEL_ORDER    = TreeOrder.LEVEL_ORDER()
    CHILDREN_ORDER = TreeOrder.CHILDREN_ORDER()
    POSITION_ORDER = TreeOrder.POSITION_ORDER()

    @staticmethod
    def check_order(order: int) -> None:
        try:
            TreeOrder(order)
        except:
            raise Exception("Wrong order value")
