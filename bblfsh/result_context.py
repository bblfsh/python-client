import typing as t

from bblfsh.aliases import ParseResponse

from bblfsh.pyuast import decode, IteratorExt, NodeExt


class ResponseError(Exception):
    pass


class ResultTypeException(Exception):
    pass


ResultMultiType = t.NewType("ResultType", t.Union[dict, int, float, bool, str])


class FilterItem:
    def __init__(self, node_ext: NodeExt) -> None:
        self._node_ext = node_ext
        self._loaded_node: t.Optional[ResultMultiType] = None

    def _ensure_load(self):
        if self._loaded_node is None:
            self._loaded_node = self._node_ext.load()

    def __str__(self):
        return str(self.get())

    def __repr__(self):
        return repr(self.get())

    def get(self) -> ResultMultiType:
        self._ensure_load()
        return self._loaded_node

    def _get_typed(self, type_: type) -> ResultMultiType:
        self._ensure_load()
        if not isinstance(self._loaded_node, type_):
            raise ResultTypeException("Expected {} result, but type is '{}'"
                                      .format(type_.__name__, type(self._loaded_node)))

    def get_bool(self) -> bool:
        return self._get_typed(bool)

    def get_float(self) -> float:
        res = self._get_typed(float)
        if isinstance(res, int):
            res = float(res)
        return res

    def get_int(self) -> int:
        return self._get_typed(int)

    def get_str(self) -> str:
        return self._get_typed(str)

    def get_dict(self) -> dict:
        return self._get_typed(dict)


class FilterResults:
    def __init__(self, iter_ext: IteratorExt) -> None:
        self._iter_ext = iter_ext

    def __iter__(self) -> object:
        return self

    def __next__(self) -> FilterItem:
        return FilterItem(next(self._iter_ext))


class ResultContext:
    def __init__(self, grpc_response: ParseResponse) -> None:
        if grpc_response.errors:
            raise ResponseError("\n".join(
                [error.text for error in grpc_response.errors])
            )

        self._response = grpc_response
        self._ctx = decode(grpc_response.uast, format=0)
        self.language = grpc_response.language

    def filter(self, query: str) -> FilterResults:
        return FilterResults(self._ctx.filter(query))

    def get_all(self) -> dict:
        return self._ctx.load()

    def __str__(self) -> str:
        return str(self.get_all())

    def __repr__(self) -> str:
        return repr(self.get_all())
