from enum import IntEnum


class TreeOrder(IntEnum):
    _MIN = 0
    # Gives no assurances over the iteration order of the tree
    # Uses the fastest one available (the one that the tree
    # natively supports)
    ANY_ORDER = 0
    PRE_ORDER = 1
    POST_ORDER = 2
    LEVEL_ORDER = 3
    CHILDREN_ORDER = 4
    POSITION_ORDER = 5
    _MAX = 3

    @staticmethod
    def check_order(order: int) -> None:
        if order < TreeOrder._MIN or order > TreeOrder._MAX:
            raise Exception("Wrong order value")
