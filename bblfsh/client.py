import os
import sys

import grpc

# The following two insertions fix the broken pb import paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__),
                                "github/com/bblfsh/sdk/protocol"))
sys.path.insert(0, os.path.dirname(__file__))
from bblfsh.github.com.bblfsh.sdk.protocol.generated_pb2 import ParseRequest
from bblfsh.github.com.bblfsh.sdk.protocol.generated_pb2_grpc import ProtocolServiceStub
from bblfsh.pyuast import Node

class BblfshClient(object):
    """
    Babelfish gRPC client. Currently it is only capable of fetching UASTs.
    """

    def __init__(self, endpoint):
        """
        Initializes a new instance of BblfshClient.

        :param endpoint: The address of the Babelfish server, \
                         for example "0.0.0.0:9432"
        :type endpoint: str
        """
        Node.initialize()
        self._channel = grpc.insecure_channel(endpoint)
        self._stub = ProtocolServiceStub(self._channel)

    def parse(self, filename, language=None, contents=None, timeout=None,
              unicode_errors="ignore"):
        """
        Queries the Babelfish server and receives the UAST response for the specified
        file.

        :param filename: The path to the file. Can be arbitrary if contents \
                          is not None.
        :param language: The programming language of the file. Refer to \
                         https://doc.bblf.sh/languages.html for the list of \
                         currently supported languages. None means autodetect.
        :param contents: The contents of the file. IF None, it is read from \
                         filename.
        :param timeout: The request timeout in seconds.
        :param unicode_errors: This is passed to open() and changes the way \
                               Unicode read errors are handled.
        :type filename: str
        :type language: str
        :type contents: str
        :type timeout: float
        :return: UAST object.
        """
        if contents is None:
            with open(filename, errors=unicode_errors) as fin:
                contents = fin.read()
        request = ParseRequest(filename=os.path.basename(filename),
                               content=contents,
                               language=self._scramble_language(language))
        return self._stub.Parse(request, timeout=timeout)

    def get_uast(self, filename, language=None, contents=None, timeout=None,
                 unicode_errors="ignore"):
        """
        Queries the Babelfish server and received the root UAST node that can be
        queried directly using libuast.

        :param filename: The path to the file. Can be arbitrary if contents \
                          is not None.
        :param language: The programming language of the file. Refer to \
                         https://doc.bblf.sh/languages.html for the list of \
                         currently supported languages. None means autodetect.
        :param contents: The contents of the file. IF None, it is read from \
                         filename.
        :param timeout: The request timeout in seconds.
        :param unicode_errors: This is passed to open() and changes the way \
                               Unicode read errors are handled.
        :type filename: str
        :type language: str
        :type contents: str
        :type timeout: float
        :return: UAST object.
        """
        response = self.parse(filename, language, contents, timeout, unicode_errors)
        return _get_from_proto(response)


    @staticmethod
    def _scramble_language(lang):
        if lang is None:
            return None
        lang = lang.lower()
        lang = lang.replace(" ", "-")
        lang = lang.replace("+", "p")
        lang = lang.replace("#", "sharp")
        return lang

def _get_from_proto(response):
    return _recursive_conv(response.uast)

def _recursive_conv(data):
    node = Node(data.internal_type)
    node.thisown = False
    node.token = data.token

    node.start_position.line = data.start_position.line
    node.start_position.col = data.start_position.col

    node.end_position.line = data.end_position.line
    node.end_position.col = data.end_position.col

    for role in data.roles:
        node.add_role(role)

    for key, value in data.properties.items():
        node.set_property(key, value)

    for child in data.children:
        node.add_child(_recursive_conv(child))

    return node
