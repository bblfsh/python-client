import os
import sys

import grpc

from bblfsh.aliases import (ParseRequest, ParseResponse, NativeParseRequest, NativeParseResponse,
        VersionRequest, ProtocolServiceStub, SupportedLanguagesRequest, SupportedLanguagesResponse)
from bblfsh.sdkversion import VERSION

# The following two insertions fix the broken pb import paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__),
                                "gopkg/in/bblfsh/sdk/%s/protocol" % VERSION))
sys.path.insert(0, os.path.dirname(__file__))


class NonUTF8ContentException(Exception):
    pass


class BblfshClient(object):
    """
    Babelfish gRPC client. Currently it is only capable of fetching UASTs.
    """

    def __init__(self, endpoint: str):
        """
        Initializes a new instance of BblfshClient.

        :param endpoint: The address of the Babelfish server, \
                         for example "0.0.0.0:9432"
        """
        self._channel = grpc.insecure_channel(endpoint)
        self._stub = ProtocolServiceStub(self._channel)

    @staticmethod
    def _check_utf8(text: str) -> None:
        try:
            text.decode("utf-8")
        except UnicodeDecodeError:
            raise NonUTF8ContentException("Content must be UTF-8, ASCII or Base64 encoded")

    @staticmethod
    def _get_contents(contents: str, filename: str) -> str:
        if contents is None:
            with open(filename, "rb") as fin:
                contents = fin.read()
        BblfshClient._check_utf8(contents)
        return contents

    def parse(self, filename: str, language: str=None, contents: str=None,
              timeout: float=None) -> ParseResponse:
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
        :return: UAST object.
        """

        contents = self._get_contents(contents, filename)
        request = ParseRequest(filename=os.path.basename(filename),
                               content=contents,
                               language=self._scramble_language(language))
        return self._stub.Parse(request, timeout=timeout)

    def native_parse(self, filename: str, language: str=None, contents: str=None,
                     timeout: float=None) -> NativeParseResponse:
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
        :return: Native AST object.
        """

        contents = self._get_contents(contents, filename)
        request = NativeParseRequest(filename=os.path.basename(filename),
                                     content=contents,
                                     language=self._scramble_language(language))
        return self._stub.NativeParse(request, timeout=timeout)

    def supported_languages(self):
        sup_response = self._stub.SupportedLanguages(SupportedLanguagesRequest())
        return sup_response.languages

    def version(self):
        """
        Queries the Babelfish server for version and runtime information.

        :return: A dictionary with the keys "version" for the semantic version and
                 "build" for the build timestamp.
        """
        return self._stub.Version(VersionRequest())

    @staticmethod
    def _scramble_language(lang: str) -> str:
        if lang is None:
            return None
        lang = lang.lower()
        lang = lang.replace(" ", "-")
        lang = lang.replace("+", "p")
        lang = lang.replace("#", "sharp")
        return lang
