from enum import IntEnum


class TreeOrder(IntEnum):
    _MIN = 0
    PRE_ORDER = 0
    POST_ORDER = 1
    LEVEL_ORDER = 2
    POSITION_ORDER = 3
    _MAX = 3

    @staticmethod
    def check_order(order: int) -> None:
        if order < TreeOrder._MIN or order > TreeOrder._MAX:
            raise Exception("Wrong order value")
