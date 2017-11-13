import os
import sys

import grpc

from bblfsh.aliases import ParseRequest, NativeParseRequest, VersionRequest, ProtocolServiceStub
from bblfsh.sdkversion import VERSION

# The following two insertions fix the broken pb import paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__),
                                "gopkg/in/bblfsh/sdk/%s/protocol" % VERSION))
sys.path.insert(0, os.path.dirname(__file__))


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
        self._channel = grpc.insecure_channel(endpoint)
        self._stub = ProtocolServiceStub(self._channel)

    def parse(self, filename, language=None, contents=None, timeout=None):
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
        :type filename: str
        :type language: str
        :type contents: str
        :type timeout: float
        :return: UAST object.
        """

        if contents is None:
            with open(filename, "rb") as fin:
                contents = fin.read()
        request = ParseRequest(filename=os.path.basename(filename),
                               content=contents,
                               language=self._scramble_language(language))
        return self._stub.Parse(request, timeout=timeout)

    def native_parse(self, filename, language=None, contents=None, timeout=None):
        """
        Queries the Babelfish server and receives the native AST response for the specified
        file.

        :param filename: The path to the file. Can be arbitrary if contents \
                         is not None.
        :param language: The programming language of the file. Refer to \
                         https://doc.bblf.sh/languages.html for the list of \
                         currently supported languages. None means autodetect.
        :param contents: The contents of the file. IF None, it is read from \
                         filename.
        :param timeout: The request timeout in seconds.
        :type filename: str
        :type language: str
        :type contents: str
        :type timeout: float
        :return: Native AST object.
        """

        if contents is None:
            with open(filename, "rb") as fin:
                contents = fin.read()
        request = NativeParseRequest(filename=os.path.basename(filename),
                               content=contents,
                               language=self._scramble_language(language))
        return self._stub.NativeParse(request, timeout=timeout)

    def version(self):
        """
        Queries the Babelfish server for version and runtime information.

        :return: A dictionary with the keys "version" for the semantic version and
                 "build" for the build timestamp.
        """
        return self._stub.Version(VersionRequest())

    @staticmethod
    def _scramble_language(lang):
        if lang is None:
            return None
        lang = lang.lower()
        lang = lang.replace(" ", "-")
        lang = lang.replace("+", "p")
        lang = lang.replace("#", "sharp")
        return lang
