import glob
import logging
import os
import pkg_resources
import re
import shutil
import subprocess
import sys
import tarfile
from urllib.request import urlopen

from setuptools import setup, find_packages, Extension
from setuptools.command.build_ext import build_ext

VERSION = "3.0.0"
LIBUAST_VERSION = "v3.1.0"
LIBUAST_ARCH = "linux-amd64"
SDK_V1_VERSION = "v1.16.1"
SDK_V1_MAJOR = SDK_V1_VERSION.split('.')[0]
SDK_V2_VERSION = "v2.15.0"
SDK_V2_MAJOR = SDK_V2_VERSION.split('.')[0]

FORMAT_ARGS = globals()

sources = ["bblfsh/pyuast.cc"]
log = logging.getLogger("setup.py")

# For debugging libuast-client interactions, set to True in production!
GET_LIBUAST = True
if not GET_LIBUAST:
    log.warning("WARNING: not retrieving libuast, using local version")


class CustomBuildExt(build_ext):
    def run(self):
        global sources

        get_libuast()
        build_ext.run(self)


def j(*paths):
    return os.path.join(*paths)


def runorexit(cmd, errmsg=""):
    log.info(">>", cmd)
    if os.system(cmd) != 0:
        sep = ". " if errmsg else ""
        log.error(errmsg + sep + "Failed command: '%s'" % cmd)
        sys.exit(1)


def mkdir(path):
    path = path.format(**FORMAT_ARGS)
    log.info("mkdir -p " + path)
    os.makedirs(path, exist_ok=True)


def rimraf(path):
    path = path.format(**FORMAT_ARGS)
    log.info("rm -rf " + path)
    shutil.rmtree(path, ignore_errors=True)


def mv(src, dst):
    src = src.format(**FORMAT_ARGS)
    dst = dst.format(**FORMAT_ARGS)
    log.info(">> mv %s %s", src, dst)
    shutil.rmtree(dst, ignore_errors=True)
    os.rename(src, dst)


def cp(src, dst):
    src = src.format(**FORMAT_ARGS)
    dst = dst.format(**FORMAT_ARGS)
    log.info(">> cp %s %s", src, dst)
    shutil.rmtree(dst, ignore_errors=True)
    shutil.copy2(src, dst)


def cpr(src, dst):
    src = src.format(**FORMAT_ARGS)
    dst = dst.format(**FORMAT_ARGS)
    log.info(">> cp -pr %s %s", src, dst)
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst, symlinks=True)


def untar_url(url, path="."):
    log.info(">> tar xf " + url)
    with urlopen(url) as response:
        # tarfile calls it only once in the beginning
        response.tell = lambda: 0
        with tarfile.open(fileobj=response, mode=("r:" + url.rsplit(".", 1)[-1])) as tar:
            tar.extractall(path=path)


def call(*cmd):
    log.info(" ".join(cmd))
    subprocess.check_call(cmd)


def create_dirs(sdk_major):
    mkdir(j("proto", "gopkg.in", "bblfsh", "sdk.%s" % sdk_major, "protocol"))
    mkdir(j("proto", "gopkg.in", "bblfsh", "sdk.%s" % sdk_major, "uast"))
    mkdir(j("bblfsh", "gopkg", "in", "bblfsh", "sdk", sdk_major, "protocol"))
    mkdir(j("bblfsh", "gopkg", "in", "bblfsh", "sdk", sdk_major, "uast"))
    mkdir(j("bblfsh", "github", "com", "gogo", "protobuf", "gogoproto"))


def create_inits(sdk_major):
    init_files = [
            j("bblfsh", "github", "__init__.py"),
            j("bblfsh", "github", "com", "__init__.py"),
            j("bblfsh", "github", "com", "gogo", "__init__.py"),
            j("bblfsh", "github", "com", "gogo", "protobuf", "__init__.py"),
            j("bblfsh", "github", "com", "gogo", "protobuf", "gogoproto", "__init__.py"),
            j("bblfsh", "gopkg", "__init__.py"),
            j("bblfsh", "gopkg", "in", "__init__.py"),
            j("bblfsh", "gopkg", "in", "bblfsh", "__init__.py"),
            j("bblfsh", "gopkg", "in", "bblfsh", "sdk", "__init__.py"),
            j("bblfsh", "gopkg", "in", "bblfsh", "sdk", sdk_major, "__init__.py"),
            j("bblfsh", "gopkg", "in", "bblfsh", "sdk", sdk_major, "uast", "__init__.py"),
            j("bblfsh", "gopkg", "in", "bblfsh", "sdk", sdk_major, "protocol", "__init__.py"),
    ]

    for f in init_files:
        open(f, "w").close()


def get_libuast():
    if not GET_LIBUAST:
        return

    gopath = os.environ.get("GOPATH")
    if not gopath:
        gopath = subprocess.check_output(
                ['go', 'env', 'GOPATH']).decode("utf-8").strip()
    if not gopath:
        log.error("GOPATH must be set")
        sys.exit(1)

    py_dir = os.getcwd()
    local_libuast = j(py_dir, "bblfsh", "libuast")
    mkdir(local_libuast)

    # Retrieve libuast
    untar_url("https://github.com/bblfsh/libuast/releases/download/%s/libuast-%s.tar.gz" % (LIBUAST_VERSION, LIBUAST_ARCH))
    mv(LIBUAST_ARCH, local_libuast)


def proto_download_v1():
    url = "https://github.com/bblfsh/sdk/archive/%s.tar.gz" % SDK_V1_VERSION
    untar_url(url)
    sdkdir = "sdk-" + SDK_V1_VERSION[1:]
    destdir = j("proto", "gopkg.in", "bblfsh", "sdk.{SDK_V1_MAJOR}")
    cp(j(sdkdir, "protocol", "generated.proto"),
        j(destdir, "protocol", "generated.proto"))
    cp(j(sdkdir, "uast", "generated.proto"),
        j(destdir, "uast", "generated.proto"))
    rimraf(sdkdir)


def proto_download_v2():
    untar_url("https://github.com/bblfsh/sdk/archive/%s.tar.gz"
              % SDK_V2_VERSION)
    sdkdir = "sdk-" + SDK_V2_VERSION[1:]
    destdir = j("proto", "gopkg.in", "bblfsh", "sdk.{SDK_V2_MAJOR}")
    cp(j(sdkdir, "protocol", "driver.proto"),
       j(destdir, "protocol", "generated.proto"))
    cp(j(sdkdir, "uast", "role", "generated.proto"),
       j(destdir, "uast", "generated.proto"))
    rimraf(sdkdir)


def proto_compile():
    sysinclude = "-I" + pkg_resources.resource_filename("grpc_tools", "_proto")
    from grpc.tools import protoc as protoc_module

    from_import_re = re.compile(r"from ((github|gopkg)\.[^ ]*) import (.*)")
    importlib_import_re = re.compile(r"([^ ]+) = importlib\.import_module\('(.*)")
    grpc_import_re = re.compile(
        r"from (([^ .]+\.)*in(\.[^ .]+)*) import ([^ ]+) as ([^\n]+)")

    def patch(file, *patchers):
        with open(file) as fin:
            code = fin.readlines()
        for i, line in enumerate(code):
            for regexp, replacer in patchers:
                match = regexp.match(line)
                if match:
                    code[i] = replacer(match)
                    log.info("patched import in %s: %s", file, match.groups()[0])
                    break
            if line.startswith("class") or line.startswith("DESCRIPTOR"):
                break
        with open(file, "w") as fout:
            fout.write("".join(code))

    def protoc(proto_file, grpc=False):
        main_args = [protoc_module.__file__, "--python_out=bblfsh"]
        target_dir = j("bblfsh", *os.path.dirname(proto_file).split("."))

        if grpc:
            # using "." creates "gopkg.in" instead of "gopkg/in" directories
            main_args += ["--grpc_python_out=" + target_dir]

        main_args += ["-Iproto", sysinclude, j("proto", proto_file)]
        log.info("%s -m grpc.tools.protoc " +
                 " ".join(main_args[1:]), sys.executable)
        protoc_module.main(main_args)

        if grpc:
            # we need to move the file back to grpc_out
            grpc_garbage_dir = None
            target = j(target_dir, "generated_pb2_grpc.py")

            for root, dirnames, filenames in os.walk(target_dir):
                for filename in filenames:

                    if filename == "generated_pb2_grpc.py" and\
                            grpc_garbage_dir is not None:
                        mv(j(root, filename), target)

                if os.path.samefile(root, target_dir):
                    grpc_garbage_dir = j(root, dirnames[0])

            if grpc_garbage_dir:
                rimraf(grpc_garbage_dir)

            # grpc ignores "in" and we need to patch the import path
            def grpc_replacer(match):
                groups = match.groups()
                return 'import importlib\n%s = importlib.import_module("bblfsh.%s.%s")\n' % (
                    groups[-1], groups[0], groups[-2])

            patch(target, (grpc_import_re, grpc_replacer))

        target = glob.glob(j(target_dir, "*_pb2.py"))[0]

        def from_import_replacer(match):
            return "from bblfsh.%s import %s\n" % (match.group(1), match.group(3))

        def importlib_import_replacer(match):
            return "%s = importlib.import_module('bblfsh.%s\n" % (match.group(1), match.group(2))

        patch(target,
              (from_import_re, from_import_replacer),
              (importlib_import_re, importlib_import_replacer))

    protoc(j("github.com", "gogo", "protobuf", "gogoproto", "gogo.proto"))

    protoc(j("gopkg.in", "bblfsh", "sdk." + SDK_V1_MAJOR, "protocol", "generated.proto"), True)
    protoc(j("gopkg.in", "bblfsh", "sdk." + SDK_V1_MAJOR, "uast", "generated.proto"))

    protoc(j("gopkg.in", "bblfsh", "sdk." + SDK_V2_MAJOR, "uast", "generated.proto"))
    protoc(j("gopkg.in", "bblfsh", "sdk." + SDK_V2_MAJOR, "protocol", "generated.proto"), True)


def do_get_deps():
    get_libuast()

    create_dirs(SDK_V1_MAJOR)
    create_dirs(SDK_V2_MAJOR)

    create_inits(SDK_V1_MAJOR)
    create_inits(SDK_V2_MAJOR)

    proto_download_v1()
    proto_download_v2()
    proto_compile()


def clean():
    rimraf("build")
    rimraf("gopkg.in")
    rimraf(j("bblfsh", "github"))
    rimraf(j("bblfsh", "gopkg"))
    if GET_LIBUAST:
        rimraf(j("bblfsh", "libuast"))


def main():
    # The --global-uast flag allows to install the python driver
    # using the installed uast library
    if "--log" in sys.argv:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.ERROR)

    if "--getdeps" in sys.argv:
        do_get_deps()
        sys.exit()

    if "--clean" in sys.argv:
        clean()
        sys.exit()

    libraries = []
    static_lib_dir = j("bblfsh", "libuast")
    static_libraries = ["{}/libuast".format(static_lib_dir)]

    if sys.platform == 'win32':
        libraries.extend(static_libraries)
        libraries.extend(["legacy_stdio_definitions", "winmm", "ws2_32"])
        extra_objects = []
    else:  # POSIX
        extra_objects = ['{}.a'.format(l) for l in static_libraries]

    libuast_module = Extension(
        "bblfsh.pyuast",
        libraries=libraries,
        extra_compile_args=["-std=c++11"],
        extra_objects=extra_objects,
        include_dirs=[j("bblfsh", "libuast")],
        sources=sources)

    setup(
        cmdclass={
            "build_ext": CustomBuildExt,
        },
        name="bblfsh",
        description="Fetches Universal Abstract Syntax Trees from Babelfish.",
        version=VERSION,
        license="Apache 2.0",
        author="source{d}",
        author_email="language-analysis@sourced.tech",
        url="https://github.com/bblfsh/client-python",
        download_url="https://github.com/bblfsh/client-python",
        packages=find_packages(),
        exclude=["bblfsh/test.py"],
        keywords=["babelfish", "uast"],
        install_requires=["grpcio>=1.13.0", "grpcio-tools>=1.13.0",
                          "docker", "protobuf>=3.4.0"],
        package_data={"": ["LICENSE", "README.md"]},
        ext_modules=[libuast_module],
        classifiers=[
            "Development Status :: 3 - Alpha",
            "Environment :: Console",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: POSIX",
            "Programming Language :: Python :: 3.4",
            "Programming Language :: Python :: 3.5",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Topic :: Software Development :: Libraries"
        ],
        zip_safe=False,
    )


if __name__ == "__main__":
    main()
