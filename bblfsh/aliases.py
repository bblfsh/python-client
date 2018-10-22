import importlib

from bblfsh.sdkversion import VERSION

# "in" is a reserved keyword in Python thus can't be used as package name, so
# we import by string

DESCRIPTOR = importlib.import_module(
        "bblfsh.gopkg.in.bblfsh.sdk.v2.uast.generated_pb2").DESCRIPTOR

# Node = importlib.import_module(
        # "bblfsh.gopkg.in.bblfsh.sdk.v2.uast.generated_pb2").Node

ParseResponse = importlib.import_module(
    "bblfsh.gopkg.in.bblfsh.sdk.v2.protocol.generated_pb2").ParseResponse

ParseError = importlib.import_module(
    "bblfsh.gopkg.in.bblfsh.sdk.v2.protocol.generated_pb2").ParseError

Mode = importlib.import_module(
    "bblfsh.gopkg.in.bblfsh.sdk.v2.protocol.generated_pb2").Mode

ParseRequest = importlib.import_module(
    "bblfsh.gopkg.in.bblfsh.sdk.v2.protocol.generated_pb2").ParseRequest

VersionRequest = importlib.import_module(
        "bblfsh.gopkg.in.bblfsh.sdk.v1.protocol.generated_pb2"
        ).VersionRequest

SupportedLanguagesRequest = importlib.import_module(
        "bblfsh.gopkg.in.bblfsh.sdk.v1.protocol.generated_pb2"
        ).SupportedLanguagesRequest

SupportedLanguagesResponse = importlib.import_module(
        "bblfsh.gopkg.in.bblfsh.sdk.v1.protocol.generated_pb2"
        ).SupportedLanguagesResponse

ProtocolServiceStub = importlib.import_module(
        "bblfsh.gopkg.in.bblfsh.sdk.v1.protocol.generated_pb2_grpc"
        ).ProtocolServiceStub

DriverStub = importlib.import_module(
        "bblfsh.gopkg.in.bblfsh.sdk.v2.protocol.generated_pb2_grpc"
        ).DriverStub

DriverServicer = importlib.import_module(
        "bblfsh.gopkg.in.bblfsh.sdk.v2.protocol.generated_pb2_grpc"
        ).DriverServicer
