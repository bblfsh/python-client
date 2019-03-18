import os
import sys
from typing import Union, List, Any, Optional

import grpc

import bblfsh.client as bcli
from bblfsh import role_id, role_name
from bblfsh.node import Node
from bblfsh.node_iterator import NodeIterator
from bblfsh.result_context import ResultContext
from bblfsh.aliases import (
    ParseRequest, ParseResponse, DriverStub, ProtocolServiceStub,
    VersionRequest, SupportedLanguagesRequest, ModeType,
    Mode, VersionResponse, DESCRIPTOR
)
from bblfsh.pyuast import uast, iterator as native_iterator
from bblfsh.tree_order import TreeOrder

if "BBLFSH_COMPAT_SHUTUP" not in os.environ:
    print("Warning: using deprecated bblfsh v1 compatibility layer.",
          file=sys.stderr)


class WrongTypeException(Exception):
    pass


class CompatParseResponse:
    def __init__(self, ctx: ResultContext, filename: str = "") -> None:
        self._res_context = ctx
        self._filename = filename

    @property
    def uast(self) -> Node:
        return self._res_context.uast

    @property
    def ast(self) -> Node:
        return self._res_context.ast

    @property
    def ctx(self) -> ResultContext:
        return self._res_context

    @property
    def elapsed(self) -> int:
        # FIXME(juanjux): check if the caller can get this, or measure it ourselves.
        return -1

    @property
    def language(self) -> str:
        return self._res_context.language

    @property
    def filename(self) -> str:
        return self._filename

    @property
    def DESCRIPTOR(self) -> Any:
        return self._res_context.ctx.DESCRIPTOR

    @property
    def errors(selfs) -> List:
        # ParseResponse would have raised an exception on errors
        return []


class CompatBblfshClient:
    def __init__(self, endpoint: Union[str, grpc.Channel]) -> None:
        self._bblfsh_cli = bcli.BblfshClient(endpoint)

        self._channel = self._bblfsh_cli._channel
        self._stub_v1 = self._bblfsh_cli._stub_v1
        self._stub_v2 = self._bblfsh_cli._stub_v2

    def _parse(self, filename: str, language: str = None, contents: str = None,
               timeout: float = None,
               mode: ModeType = Mode.Value('ANNOTATED')) -> CompatParseResponse:

        if timeout is not None:
            timeout = int(timeout)

        res = self._bblfsh_cli.parse(filename, language, contents,
                                     mode=mode, timeout=timeout)
        return CompatParseResponse(res, filename)

    def parse(self, filename: str, language: str = None, contents: str = None,
              timeout: float = None) -> CompatParseResponse:

        return self._parse(filename, language, contents, timeout,
                           Mode.Value('ANNOTATED'))

    def native_parse(self, filename: str, language: str = None,
                     contents: str = None,
                     timeout: float = None) -> CompatParseResponse:

        return self._parse(filename, language, contents, timeout,
                           Mode.Value('NATIVE'))

    def supported_languages(self) -> List[str]:
        return self._bblfsh_cli.supported_languages()

    def version(self) -> VersionResponse:
        return self._bblfsh_cli.version()

    def close(self) -> None:
        return self._bblfsh_cli.close()


class CompatNodeIterator:
    def __init__(
            self,
            nodeit: NodeIterator,
            only_nodes: bool = False
    ) -> None:
        self._nodeit = nodeit
        self._only_nodes = only_nodes
        # Used to forward calls of the old Node object
        # Check if this, and properties(), are needed
        self._last_node: Optional[Node] = None

    def __iter__(self) -> 'CompatNodeIterator':
        return self

    def __next__(self) -> Node:
        next_val = next(self._nodeit)

        is_node = isinstance(next_val, Node)
        val = next_val.internal_node if is_node else next_val

        # Skip positions and non dicts/lists, the later if only_nodes = True
        skip = False
        if isinstance(val, dict):
            if "@type" not in val or val["@type"] == "uast:Positions":
                skip = True
        elif self._only_nodes:
            skip = True

        if skip:
            val = self.__next__().internal_node

        ret_val = next_val if is_node else Node(value=val)
        self._last_node = ret_val
        return ret_val

    def filter(self, query: str) -> Optional['CompatNodeIterator']:
        if not self._last_node:
            return None

        return filter(self._last_node, query)

    @property
    def properties(self) -> dict:
        if isinstance(self._last_node, dict):
            return self._last_node.keys()
        else:
            return {}


def iterator(n: Union[Node, CompatNodeIterator], order: TreeOrder = TreeOrder.PRE_ORDER)\
        -> CompatNodeIterator:

    if isinstance(n, CompatNodeIterator):
        return CompatNodeIterator(n._nodeit.iterate(order), only_nodes=True)
    elif isinstance(n, Node):
        nat_it = native_iterator(n.internal_node, order)
        return CompatNodeIterator(NodeIterator(nat_it), only_nodes=True)
    elif isinstance(n, dict):
        nat_it = native_iterator(n, order)
        return CompatNodeIterator(NodeIterator(nat_it, uast()), only_nodes=True)
    else:
        raise WrongTypeException(
            "iterator on non node or iterator type (%s)" % str(type(n))
        )


def filter(n: Node, query: str) -> CompatNodeIterator:
    ctx = uast()
    return CompatNodeIterator(NodeIterator(ctx.filter(query, n.internal_node), ctx))


def filter_nodes(n: Node, query: str) -> CompatNodeIterator:
    return CompatNodeIterator(filter(n, query)._nodeit, only_nodes=True)


class TypedQueryException(Exception):
    pass


def _scalariter2item(n: Node, query: str, wanted_type: type) -> Any:
    rlist = list(filter(n, query))

    if len(rlist) > 1:
        raise TypedQueryException("More than one result for %s typed query" % str(type))

    value = rlist[0]
    if isinstance(value, Node):
        value = value.internal_node

    value_type = type(value)
    if wanted_type == float and value_type == int:
        value = float(value)

    if not isinstance(value, wanted_type):
        raise TypedQueryException("Typed query for type %s returned type %s instead"
                        % (str(wanted_type), str(type(value))))

    return wanted_type(value)


def filter_string(n: Node, query: str) -> str:
    return _scalariter2item(n, query, str)


def filter_bool(n: Node, query: str) -> bool:
    return _scalariter2item(n, query, bool)


def filter_int(n: Node, query: str) -> int:
    return _scalariter2item(n, query, int)


def filter_float(n: Node, query: str) -> float:
    return _scalariter2item(n, query, float)


filter_number = filter_float
