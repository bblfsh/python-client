import importlib
import google

# "in" is a reserved keyword in Python thus can't be used as package name, so
# we import by string
uast_v2_module = importlib.import_module(
    "bblfsh.gopkg.in.bblfsh.sdk.v2.uast.generated_pb2")
protocol_v2_module = importlib.import_module(
    "bblfsh.gopkg.in.bblfsh.sdk.v2.protocol.generated_pb2")
protocol_grpc_v2_module = importlib.import_module(
    "bblfsh.gopkg.in.bblfsh.sdk.v2.protocol.generated_pb2_grpc")

DESCRIPTOR = uast_v2_module.DESCRIPTOR

ParseRequest = protocol_v2_module.ParseRequest
ParseResponse = protocol_v2_module.ParseResponse
ParseError = protocol_v2_module.ParseError

Mode = protocol_v2_module.Mode
ModeType = google.protobuf.internal.enum_type_wrapper.EnumTypeWrapper

Manifest = protocol_v2_module.Manifest
SupportedLanguagesRequest = protocol_v2_module.SupportedLanguagesRequest
SupportedLanguagesResponse = protocol_v2_module.SupportedLanguagesResponse

VersionRequest = protocol_v2_module.VersionRequest
VersionResponse = protocol_v2_module.VersionResponse

DriverStub = protocol_grpc_v2_module.DriverStub
DriverHostStub = protocol_grpc_v2_module.DriverHostStub

class Modes:
    pass

# Current values: {'DEFAULT_MODE': 0, 'NATIVE': 1, 'PREPROCESSED': 2, 'ANNOTATED': 4, 'SEMANTIC': 8}
for k, v in Mode.DESCRIPTOR.values_by_name.items():
    setattr(Modes, k, v.number)
