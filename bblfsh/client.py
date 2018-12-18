import os
from typing import Optional, Union, List

import grpc

from bblfsh.aliases import (ParseRequest, DriverStub, ProtocolServiceStub,
                            VersionRequest, SupportedLanguagesRequest, ModeType,
                            VersionResponse)
from bblfsh.result_context import ResultContext


class NonUTF8ContentException(Exception):
    pass


class BblfshClient:
    """
    Babelfish gRPC client.
    """

    def __init__(self, endpoint: Union[str, grpc.Channel]) -> None:
        """
        Initializes a new instance of BblfshClient.

        :param endpoint: The address of the Babelfish server, \
                         for example "0.0.0.0:9432"
        :type endpoint: str
        """

        if isinstance(endpoint, str):
            self._channel = grpc.insecure_channel(endpoint)
        else:
            self._channel = grpc.endpoint

        self._stub_v1 = ProtocolServiceStub(self._channel)
        self._stub_v2 = DriverStub(self._channel)

    @staticmethod
    def _ensure_utf8(text: bytes) -> str:
        try:
            return text.decode("utf-8")
        except UnicodeDecodeError:
            raise NonUTF8ContentException("Content must be UTF-8, ASCII or Base64 encoded")

    @staticmethod
    def _get_contents(contents: Optional[Union[str, bytes]], filename: str) -> str:
        if contents is None:
            with open(filename, "rb") as fin:
                contents = fin.read()

        if isinstance(contents, bytes):
            contents = BblfshClient._ensure_utf8(contents)

        return contents

    def parse(self, filename: str, language: Optional[str]=None,
              contents: Optional[str]=None, mode: Optional[ModeType]=None,
              timeout: Optional[int]=None) -> ResultContext:
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
        :param mode:     UAST transformation mode.
        :param raw:      Return raw binary UAST without decoding it.
        :param timeout: The request timeout in seconds.
        :type filename: str
        :type language: str
        :type contents: str
        :type timeout: float
        :return: UAST object.
        """

        # TODO: handle syntax errors
        contents = self._get_contents(contents, filename)
        request = ParseRequest(filename=os.path.basename(filename),
                               content=contents, mode=mode,
                               language=self._scramble_language(language))
        response = self._stub_v2.Parse(request, timeout=timeout)
        return ResultContext(response)

    def supported_languages(self) -> List[str]:
        sup_response = self._stub_v1.SupportedLanguages(SupportedLanguagesRequest())
        return sup_response.languages

    def version(self) -> VersionResponse:
        """
        Queries the Babelfish server for version and runtime information.

        :return: A dictionary with the keys "version" for the semantic version and
                 "build" for the build timestamp.
        """
        return self._stub_v1.Version(VersionRequest())

    @staticmethod
    def _scramble_language(lang: Optional[str]) -> Optional[str]:
        if lang is None:
            return None
        lang = lang.lower()
        lang = lang.replace(" ", "-")
        lang = lang.replace("+", "p")
        lang = lang.replace("#", "sharp")
        return lang

    def close(self) -> None:
        """
        Close the gRPC channel and free the acquired resources. Using a closed client is
        not supported.
        """
        self._channel.close()
        self._channel = self._stub_v1 = self._stub_v2 = None
