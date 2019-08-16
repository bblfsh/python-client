from enum import IntEnum
from bblfsh.pyuast import AnyOrder, PreOrder, PostOrder, LevelOrder, ChildrenOrder, PositionOrder

class TreeOrder(IntEnum):
    # Gives no assurances over the iteration order of the tree
    # Uses the fastest one available (the one that the tree
    # natively supports)
    ANY_ORDER      = AnyOrder
    PRE_ORDER      = PreOrder
    POST_ORDER     = PostOrder
    LEVEL_ORDER    = LevelOrder
    CHILDREN_ORDER = ChildrenOrder
    POSITION_ORDER = PositionOrder

    @staticmethod
    def check_order(order: int) -> None:
        try:
            TreeOrder(order)
        except:
            raise Exception("Wrong order value")
