## client-python [![Build Status](https://travis-ci.org/bblfsh/client-python.svg?branch=master)](https://travis-ci.org/bblfsh/client-python) [![PyPI](https://img.shields.io/pypi/v/bblfsh.svg)](https://pypi.python.org/pypi/bblfsh)

[Babelfish](https://doc.bblf.sh) Python client library provides functionality to both
connect to the Babelfish bblfshd to parse code
(obtaining an [UAST](https://doc.bblf.sh/uast/specification.html) as a result)
and to analyse UASTs with the functionality provided by [libuast](https://github.com/bblfsh/libuast).

## Installation

The recommended way to install *client-python* is using our pip [package](https://pypi.python.org/pypi/bblfsh):

```sh
pip install bblfsh
```

### From sources

```bash
git clone https://github.com/bblfsh/client-python.git
cd client-python
python setup.py install
```

### Dependencies

You need to install `libxml2` and its header files. You also will need a `curl` cli tool to dowload `libuast`, and a `g++` for building [libtuast Python bindings](https://github.com/bblfsh/client-python/blob/0037d762563ab49b3daac8a7577f7103a5628fc6/setup.py#L17). 
The command for Debian and derived distributions would be:

```bash
sudo apt install libxml2-dev
sudo apt install curl
sudo apt install build-essential
```

## Usage

A small example of how to parse a Python file and extract the import declarations from the [UAST](https://doc.bblf.sh/uast/specification.html).

If you don't have a bblfsh server running you can execute it using the following command:

```sh
docker run --privileged --rm -it -p 9432:9432 -v bblfsh_cache:/var/lib/bblfshd --name bblfshd bblfsh/bblfshd
docker exec -it bblfshd bblfshctl driver install python bblfsh/python-driver:latest
```

Please, read the [getting started](https://doc.bblf.sh/using-babelfish/getting-started.html) guide to learn more about how to use and deploy a bblfshd.

```python
import bblfsh

client = bblfsh.BblfshClient("0.0.0.0:9432")
uast = client.parse("/path/to/file.py").uast
print(uast)
# "filter' allows you to use XPath queries to filter on result nodes:
print(bblfsh.filter(uast, "//Import[@roleImport and @roleDeclaration]//alias")

# filter\_[bool|string|number] must be used when using XPath functions returning
# these types:
print(bblfsh.filter_bool(uast, "boolean(//*[@strtOffset or @endOffset])"))
print(bblfsh.filter_string(uast, "name(//*[1])"))
print(bblfsh.filter_number(uast, "count(//*)"))

# You can also iterate on several tree iteration orders:
it = bblfsh.iterator(uast, bblfsh.TreeOrder.PRE_ORDER)
for node in it:
    print(node.internal_type)
```

Please read the [Babelfish clients](https://doc.bblf.sh/using-babelfish/language-clients.html)
guide section to learn more about babelfish clients and their query language.

## License

Apache License 2.0, see [LICENSE](LICENSE)
