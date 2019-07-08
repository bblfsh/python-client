## python-client [![Build Status](https://travis-ci.com/bblfsh/python-client.svg?branch=master)](https://travis-ci.com/bblfsh/python-client) [![PyPI](https://img.shields.io/pypi/v/bblfsh.svg)](https://pypi.python.org/pypi/bblfsh)

[Babelfish](https://doc.bblf.sh) Python client library provides functionality to both
connect to the Babelfish daemon (`bblfshd`) to parse code
(obtaining an [UAST](https://doc.bblf.sh/uast/uast-specification.html) as a result)
and to analyse UASTs with the functionality provided by [libuast](https://github.com/bblfsh/libuast).

## Installation

The recommended way to install *python-client* is using our pip [package](https://pypi.python.org/pypi/bblfsh):

```sh
pip3 install bblfsh
```

### From sources

```bash
git clone https://github.com/bblfsh/python-client.git
cd python-client
pip3 install -r requirements.txt
python3 setup.py --getdeps
python3 setup.py install
# or: pip3 install .
```

### Dependencies

You also will need a `curl` cli tool to dowload `libuast`, and a `g++` for building [libuast Python bindings](https://github.com/bblfsh/python-client/blob/c17d9cb6cd3e55ad150bd1d62a1de2e228d7db04/setup.py#L26).
The command for Debian and derived distributions would be:

```bash
sudo apt install curl build-essential
```

## Usage

A small example of how to parse a Python file and extract the import declarations from the [UAST](https://doc.bblf.sh/uast/uast-specification.html).

If you don't have a bblfsh server running you can execute it using the following command:

```sh
docker run --privileged --rm -it -p 9432:9432 -v bblfsh_cache:/var/lib/bblfshd --name bblfshd bblfsh/bblfshd
```

To parse Python files you will also need a python driver installed on bblfsh server:

```sh
docker exec -it bblfshd bblfshctl driver install python bblfsh/python-driver
```

List of all available drivers you can find at the [official documentation](https://doc.bblf.sh/languages.html).


Please, read the [getting started](https://doc.bblf.sh/using-babelfish/getting-started.html) guide to learn more about how to use and deploy a bblfshd.

### Parsing a file

```python
import bblfsh

client = bblfsh.BblfshClient("localhost:9432")
ctx = client.parse("/path/to/file.py")
print(ctx)

# You can also get the non semantic UAST or native AST:
ctx = client.parse("file.py", mode=bblfsh.Modes.NATIVE)
# Possible values for Modes: DEFAULT_MODE, NATIVE, PREPROCESSED, ANNOTATED, SEMANTIC
```

To get the UAST as a dictionary:

```python
ast = ctx.get_all()
```

### UAST filtering (XPath)

`ctx.filter()` allows you to use XPath queries to filter on result nodes:

```python
it = ctx.filter("//python:Call")
for node in it:
    # print internal node:
    print(node)
    # or get as Python dictionary/value:
    doSomething(node.get())
```

XPath queries can return different types (`dict`, `int`, `float`, `bool` or `str`),
calling `get()` with an item will return the right type, but if you must ensure
that you are getting the expected type (to avoid errors in the queries) there
are alternative typed versions:

```python
x = next(ctx.filter("boolean(//*[@startOffset or @endOffset])")).get_bool()
y = next(ctx.filter("name(//*[1])")).get_str()
z = next(ctx.filter("count(//*)")).get_int() # or get_float()
```

### Iteration

You can also iterate using iteration orders different than the
default pre-order using the `iterate` method on `parse` result or node objects:

```python
# Directly over parse results
it = client.parse("/path/to/file.py").iterate(bblfsh.TreeOrder.POST_ORDER)
for node in it:
    print(node)

# Over filter results (which by default are already iterators with PRE_ORDER):
ctx = client.parse("file.py")
it = ctx.filter("//python:Call").iterate(bblfsh.TreeOrder.LEVEL_ORDER)
for node in it:
    print(node)

# Over individual node objects to change the iteration order of
# a specific subtree:
ast = ctx.root
it = ast.iterate(bblfsh.TreeOrder.POSITION_ORDER)
for node in it:
    print(node)
```

Please read the [Babelfish clients](https://doc.bblf.sh/using-babelfish/clients.html)
guide section to learn more about babelfish clients and their query language.

## License

Apache License 2.0, see [LICENSE](LICENSE)
