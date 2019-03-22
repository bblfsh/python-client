"""
This file provides a compatibility layer with the old UAST V1 (or client-python
v2) API. You can see a summary of that API here:

https://github.com/bblfsh/client-python/blob/d485273f457a174b40b820ad71195a739db04197/README.md

Note that this won't translate the XPath queries from the old projection to the new use;
even when using this module you're expected to use expressions matching the new
projection.

Note that since this is a pure Python translation layer, some performance
impact is to be expected.
"""
import os
import sys
from typing import Union, List, Any, Optional

import grpc

import bblfsh.client as newbbl
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

print("Warning: using deprecated bblfsh v1 compatibility layer.", file=sys.stderr)


class WrongTypeException(Exception):
    """
    This exception is raised when the API receives an unexpected type
    """
    pass


class CompatParseResponse:
    """
    This class emulates the API of the old ParseResponse object.
    """
    def __init__(self, ctx: ResultContext, filename: str = "") -> None:
        self._res_context = ctx
        self._filename = filename

    @property
    def uast(self) -> Node:
        """
        Returns the root Node.
        """
        return self._res_context.uast

    @property
    def ast(self) -> Node:
        """
        Returns the root Node. This is provided for compatibility, but
        since the type of result is now expecified using CompatBblfshClient.parse
        or parse_native, it'll return the same as uast().
        """
        return self._res_context.ast

    @property
    def ctx(self) -> ResultContext:
        """
        Returns the ResultContext of the response.
        """
        return self._res_context

    @property
    def elapsed(self) -> int:
        """
        Provided for compatibility, but since the new API's ParseResponse doesn't
        provide an elapsed time it'll always return -1.
        """
        # FIXME(juanjux): check if the caller can get this, or measure it ourselves.
        return -1

    @property
    def language(self) -> str:
        """
        Returns the language used for the request.
        """
        return self._res_context.language

    @property
    def filename(self) -> str:
        """
        Returns the filename used for the request.
        """
        return self._filename

    @property
    def DESCRIPTOR(self) -> Any:
        """
        Returns the gRPC context descriptor.
        """
        return self._res_context.ctx.DESCRIPTOR

    @property
    def errors(selfs) -> List:
        """
        Provided for compatibility. Since the new API will raise exceptions on errors,
        this just returns and empty array.
        """
        # ParseResponse would have raised an exception on errors
        return []


class CompatBblfshClient:
    """
    This emulates the methods and properties of the old BblfshClient.
    """
    def __init__(self, endpoint: Union[str, grpc.Channel]) -> None:
        """
        Connects to the specified grpc endpoint which can be specified either as
        a grpc Channel object or a connection string (like "0.0.0.0:6432").
        """
        self._bblfsh_cli = newbbl.BblfshClient(endpoint)

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

        """
        Parse the specified filename or contents and return a CompatParseResponse.
        """

        return self._parse(filename, language, contents, timeout,
                           Mode.Value('ANNOTATED'))

    def native_parse(self, filename: str, language: str = None,
                     contents: str = None,
                     timeout: float = None) -> CompatParseResponse:
        """
        Same as parse() but the returned response will include only the native
        (non annotated) AST.
        """

        return self._parse(filename, language, contents, timeout,
                           Mode.Value('NATIVE'))

    def supported_languages(self) -> List[str]:
        """
        Return a list of the languages that can be parsed by the connected
        endpoint (driver or bblfsh daemon).
        """
        return self._bblfsh_cli.supported_languages()

    def version(self) -> VersionResponse:
        """
        Returns the connected endpoint version.
        """
        return self._bblfsh_cli.version()

    def close(self) -> None:
        """
        Closes the connection to the endpoint.
        """
        return self._bblfsh_cli.close()


class CompatNodeIterator:
    """
    This emulates the API of the pre-v3 iterators.
    """
    def __init__(self, nodeit: NodeIterator, only_nodes: bool = False) -> None:
        """
        Creates a CompatNodeIterator compatibility object using a NodeIterator
        from the post-v3 API. If the only_nodes parameter is set to true,
        scalars and strings won't be included in the results.
        """
        self._nodeit = nodeit
        self._only_nodes = only_nodes
        # Used to forward calls of the old Node object
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
        """
        Further filter the results using this iterator as base.
        """
        if not self._last_node:
            return None

        return filter(self._last_node, query)

    @property
    def properties(self) -> dict:
        """
        Returns the properties of the current node in the iteration.
        """
        if isinstance(self._last_node, dict):
            return self._last_node.keys()
        else:
            return {}


def iterator(n: Union[Node, CompatNodeIterator, dict],
        order: TreeOrder = TreeOrder.PRE_ORDER) -> CompatNodeIterator:
    """
    This function has the same signature as the pre-v3 iterator()
    call returning a compatibility CompatNodeIterator.
    """

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
    """
    This function has the same signature as the pre-v3 filter() returning a
    compatibility CompatNodeIterator.
    """
    ctx = uast()
    return CompatNodeIterator(NodeIterator(ctx.filter(query, n.internal_node), ctx))


def filter_nodes(n: Node, query: str) -> CompatNodeIterator:
    """
    Utility function. Same as filter() but will only filter for nodes (i. e.
    it will exclude scalars and positions).
    """
    return CompatNodeIterator(filter(n, query)._nodeit, only_nodes=True)


class TypedQueryException(Exception):
    """
    This exception will be raised when a query for a specific type (str, int, float...)
    returns a different type of more than one result.
    """
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
    """
    Filter and ensure that the returned value is of string type.
    """
    return _scalariter2item(n, query, str)


def filter_bool(n: Node, query: str) -> bool:
    """
    Filter and ensure that the returned value is of type bool.
    """
    return _scalariter2item(n, query, bool)


def filter_int(n: Node, query: str) -> int:
    """
    Filter and ensure that the returned value is of type int.
    """
    return _scalariter2item(n, query, int)


def filter_float(n: Node, query: str) -> float:
    """
    Filter and ensure that the returned value is of type int.
    """
    return _scalariter2item(n, query, float)


filter_number = filter_float
