__all__ = ["DESCRIPTOR", "Node", "ParseResponse", "NativeParseResponse",
           "ParseRequest", "NativeParseRequest", "VersionRequest",
           "ProtocolServiceStub"]

import importlib

from bblfsh.sdkversion import VERSION

# "in" is a reserved keyword in Python thus can't be used as package name, so
# we import by string

DESCRIPTOR = importlib.import_module(
        "bblfsh.gopkg.in.bblfsh.sdk.%s.uast.generated_pb2" % VERSION).DESCRIPTOR

Node = importlib.import_module(
        "bblfsh.gopkg.in.bblfsh.sdk.%s.uast.generated_pb2" % VERSION).Node

ParseResponse = importlib.import_module(
    "bblfsh.gopkg.in.bblfsh.sdk.%s.protocol.generated_pb2" % VERSION).ParseResponse

NativeParseResponse = importlib.import_module(
        "bblfsh.gopkg.in.bblfsh.sdk.%s.protocol.generated_pb2" % VERSION
        ).NativeParseResponse

ParseRequest = importlib.import_module(
    "bblfsh.gopkg.in.bblfsh.sdk.%s.protocol.generated_pb2" % VERSION).ParseRequest

NativeParseRequest = importlib.import_module(
        "bblfsh.gopkg.in.bblfsh.sdk.%s.protocol.generated_pb2" % VERSION
        ).NativeParseRequest

VersionRequest = importlib.import_module(
        "bblfsh.gopkg.in.bblfsh.sdk.%s.protocol.generated_pb2" % VERSION
        ).VersionRequest

SupportedLanguagesRequest = importlib.import_module(
        "bblfsh.gopkg.in.bblfsh.sdk.%s.protocol.generated_pb2" % VERSION
        ).SupportedLanguagesRequest

SupportedLanguagesResponse = importlib.import_module(
        "bblfsh.gopkg.in.bblfsh.sdk.%s.protocol.generated_pb2" % VERSION
        ).SupportedLanguagesResponse

ProtocolServiceStub = importlib.import_module(
        "bblfsh.gopkg.in.bblfsh.sdk.%s.protocol.generated_pb2_grpc" % VERSION
        ).ProtocolServiceStub
