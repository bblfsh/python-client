import os
import sys

import grpc

# The following two insertions fix the broken pb import paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__),
                                "github/com/bblfsh/sdk/protocol"))
sys.path.insert(0, os.path.dirname(__file__))
from bblfsh.github.com.bblfsh.sdk.protocol.generated_pb2 import ParseUASTRequest
from bblfsh.github.com.bblfsh.sdk.protocol.generated_pb2_grpc import ProtocolServiceStub


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

    def fetch_uast(self, file_path, language, contents=None):
        """
        Queries the Babelfish server and receives the UAST for the specified
        file.

        :param file_path: The path to the file. Can be arbitrary if contents \
                          is not None.
        :param language: The programming language of the file. Refer to \
                         https://doc.bblf.sh/languages.html for the list of \
                         currently supported languages.
        :param contents: The contents of the file. IF None, it is read from \
                         file_path.
        :type file_path: str
        :type language: str
        :type contents: str
        :return: UAST object.
        """
        if contents is None:
            with open(file_path) as fin:
                contents = fin.read()
        request = ParseUASTRequest(filename=os.path.basename(file_path),
                                   content=contents,
                                   language=self._scramble_language(language))
        response = self._stub.ParseUAST(request)
        return response

    @staticmethod
    def _scramble_language(lang):
        lang = lang.lower()
        lang = lang.replace(" ", "-")
        lang = lang.replace("+", "p")
        lang = lang.replace("#", "sharp")
        return lang
