__all__ = ["DESCRIPTOR", "Node", "Position", "ParseResponse", "NativeParseResponse",
           "ParseRequest", "NativeParseRequest", "VersionRequest", "ProtocolServiceStub"]

import importlib

from bblfsh.sdkversion import VERSION

# "in" is a reserved keyword in Python thus can't be used as package name, so
# we import by string
uast_module = importlib.import_module(
    "bblfsh.gopkg.in.bblfsh.sdk.%s.uast.generated_pb2" % VERSION)
protocol_module = importlib.import_module(
    "bblfsh.gopkg.in.bblfsh.sdk.%s.protocol.generated_pb2" % VERSION)
protocol_grpc_module = importlib.import_module(
    "bblfsh.gopkg.in.bblfsh.sdk.%s.protocol.generated_pb2_grpc" % VERSION)

DESCRIPTOR = uast_module.DESCRIPTOR
Node = uast_module.Node
Position = uast_module.Position
ParseResponse = protocol_module.ParseResponse
NativeParseResponse = protocol_module.NativeParseResponse
ParseRequest = protocol_module.ParseRequest
NativeParseRequest = protocol_module.NativeParseRequest
VersionRequest = protocol_module.VersionRequest
SupportedLanguagesRequest = protocol_module.SupportedLanguagesRequest
SupportedLanguagesResponse = protocol_module.SupportedLanguagesResponse
ProtocolServiceStub = protocol_grpc_module.ProtocolServiceStub
