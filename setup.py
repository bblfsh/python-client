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

VERSION = "2.12.7"
LIBUAST_VERSION = "v1.9.5"
SDK_VERSION = "v1.16.1"
SDK_MAJOR = SDK_VERSION.split('.')[0]
FORMAT_ARGS = globals()

# For debugging libuast-client interactions, set to True in production!
GET_LIBUAST = True
if not GET_LIBUAST:
    print("WARNING: not retrieving libuast, using local version")

if os.getenv("CC") is None:
    os.environ["CC"] = "g++"  # yes, g++ - otherwise distutils will use gcc -std=c++11 and explode
if os.getenv("CXX") is None:
    os.environ["CXX"] = "g++"
libraries = ['xml2']
sources = ["bblfsh/pyuast.cc", "bblfsh/memtracker.cc"]
log = logging.getLogger("setup.py")


class CustomBuildExt(build_ext):
    def run(self):
        global libraries
        global sources

        if "--global-uast" in sys.argv:
            libraries.append("uast")
        else:
            sources.append("bblfsh/libuast/uast.cc")
            sources.append("bblfsh/libuast/roles.c")

        get_libuast()
        build_ext.run(self)


def j(*paths):
    return os.path.join(*paths)


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
    log.info("mv %s %s", src, dst)
    shutil.rmtree(dst, ignore_errors=True)
    os.rename(src, dst)


def cp(src, dst):
    src = src.format(**FORMAT_ARGS)
    dst = dst.format(**FORMAT_ARGS)
    log.info("cp -p %s %s", src, dst)
    shutil.rmtree(dst, ignore_errors=True)
    shutil.copy2(src, dst)


def cpr(src, dst):
    src = src.format(**FORMAT_ARGS)
    dst = dst.format(**FORMAT_ARGS)
    log.info("cp -pr %s %s", src, dst)
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst, symlinks=True)


def untar_url(url, path="."):
    log.info("tar xf " + url)
    with urlopen(url) as response:
        response.tell = lambda: 0  # tarfile calls it only once in the beginning
        with tarfile.open(fileobj=response, mode=("r:" + url.rsplit(".", 1)[-1])) as tar:
            tar.extractall(path=path)


def call(*cmd):
    log.info(" ".join(cmd))
    subprocess.check_call(cmd)


def create_dirs():
    mkdir(j("proto", "gopkg.in", "bblfsh", "sdk.{SDK_MAJOR}", "protocol"))
    mkdir(j("proto", "gopkg.in", "bblfsh", "sdk.{SDK_MAJOR}", "uast"))
    mkdir(j("bblfsh", "gopkg", "in", "bblfsh", "sdk", SDK_MAJOR, "protocol"))
    mkdir(j("bblfsh", "gopkg", "in", "bblfsh", "sdk", SDK_MAJOR, "uast"))
    mkdir(j("bblfsh", "github", "com", "gogo", "protobuf", "gogoproto"))


def create_inits():
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
            j("bblfsh", "gopkg", "in", "bblfsh", "sdk", SDK_MAJOR, "__init__.py"),
            j("bblfsh", "gopkg", "in", "bblfsh", "sdk", SDK_MAJOR, "uast", "__init__.py"),
            j("bblfsh", "gopkg", "in", "bblfsh", "sdk", SDK_MAJOR, "protocol", "__init__.py"),
    ]

    for f in init_files:
        open(f, "w").close()


def get_libuast():
    if not GET_LIBUAST:
        return

    untar_url(
        "https://github.com/bblfsh/libuast/archive/{LIBUAST_VERSION}/{LIBUAST_VERSION}.tar.gz"
        .format(**FORMAT_ARGS))
    mv("libuast-" + LIBUAST_VERSION.replace("v", ""), "libuast")
    cpr(j("libuast", "src"), j("bblfsh", "libuast"))
    rimraf("libuast")


def proto_download():
    untar_url("https://github.com/bblfsh/sdk/archive/%s.tar.gz" % SDK_VERSION)
    sdkdir = "sdk-" + SDK_VERSION[1:]
    destdir = j("proto", "gopkg.in", "bblfsh", "sdk.{SDK_MAJOR}")
    cp(j(sdkdir, "protocol", "generated.proto"), j(destdir, "protocol", "generated.proto"))
    cp(j(sdkdir, "uast", "generated.proto"), j(destdir, "uast", "generated.proto"))
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
        log.info("%s -m grpc.tools.protoc " + " ".join(main_args[1:]), sys.executable)
        protoc_module.main(main_args)
        if grpc:
            # we need to move the file back to grpc_out
            grpc_garbage_dir = None
            target = j(target_dir, "generated_pb2_grpc.py")
            for root, dirnames, filenames in os.walk(target_dir):
                for filename in filenames:
                    if filename == "generated_pb2_grpc.py" and grpc_garbage_dir is not None:
                        mv(j(root, filename), target)
                if os.path.samefile(root, target_dir):
                    grpc_garbage_dir = j(root, dirnames[0])
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

    protoc(j("gopkg.in", "bblfsh", "sdk." + SDK_MAJOR, "protocol", "generated.proto"), True)
    protoc(j("github.com", "gogo", "protobuf", "gogoproto", "gogo.proto"))
    protoc(j("gopkg.in", "bblfsh", "sdk." + SDK_MAJOR, "uast", "generated.proto"))


def do_get_deps():
    get_libuast()
    create_dirs()
    create_inits()
    proto_download()
    proto_compile()


def clean():
    rimraf("gopkg.in")
    rimraf(j("bblfsh", "github"))
    rimraf(j("bblfsh", "gopkg"))
    if GET_LIBUAST:
        rimraf(j("bblfsh", "libuast"))


def main():
    # The --global-uast flag allows to install the python driver using the installed uast library
    if "--log" in sys.argv:
        logging.basicConfig(level=logging.INFO)

    if "--getdeps" in sys.argv:
        do_get_deps()
        sys.exit()

    if "--clean" in sys.argv:
        clean()
        sys.exit()

    libuast_module = Extension(
        "bblfsh.pyuast",
        libraries=libraries,
        library_dirs=["/usr/lib", "/usr/local/lib"],
        extra_compile_args=["-std=c++11"],
        include_dirs=[j("bblfsh", "libuast"), "/usr/local/include", "/usr/local/include/libxml2",
                      "/usr/include", "/usr/include/libxml2"], sources=sources)

    setup(
        cmdclass = {
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
        install_requires=["grpcio>=1.13.0,<2.0", "grpcio-tools>=1.13.0,<2.0", "docker", "protobuf>=3.4.0"],
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
        ]
    )


if __name__ == "__main__":
    main()
