import sys
from setuptools import setup, find_packages, Extension

LIBRARIES = ['xml2']
SOURCES = ['bblfsh/pyuast.c']

# The --global-uast flag allows to install the python driver using the installed uast library
if "--global-uast" in sys.argv:
    LIBRARIES.append('uast')
else:
    SOURCES.append('bblfsh/libuast/uast.c')
    SOURCES.append('bblfsh/libuast/roles.c')


uast_module = Extension(
    'bblfsh._pyuast',
    libraries=LIBRARIES,
    library_dirs=['/usr/lib', '/usr/local/lib'],
    include_dirs=['libuast/src','/usr/local/include', '/usr/local/include/libxml2', '/usr/include', '/usr/include/libxml2'],
    sources=SOURCES)

setup(
    name="bblfsh",
    description="Fetches Universal Abstract Syntax Trees from Babelfish.",
    version="0.0.4",
    license="Apache 2.0",
    author="Vadim Markovtsev",
    author_email="vadim@sourced.tech",
    url="https://github.com/bblfsh/client-python",
    download_url='https://github.com/bblfsh/client-python',
    packages=find_packages(),
    exclude=["bblfsh/test.py"],
    keywords=["babelfish", "uast"],
    install_requires=["grpcio", "docker"],
    package_data={"": ["LICENSE", "README.md"]},
    ext_modules=[uast_module],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Software Development :: Libraries"
    ]
)
