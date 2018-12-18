## client-python [![Build Status](https://travis-ci.org/bblfsh/client-python.svg?branch=master)](https://travis-ci.org/bblfsh/client-python) [![PyPI](https://img.shields.io/pypi/v/bblfsh.svg)](https://pypi.python.org/pypi/bblfsh)

[Babelfish](https://doc.bblf.sh) Python client library provides functionality to both
connect to the Babelfish bblfshd to parse code
(obtaining an [UAST](https://doc.bblf.sh/uast/uast-specification.html) as a result)
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
pip install -r requirements.txt
python setup.py --getdeps
python setup.py install
# or: pip install .
```

### Dependencies

You also will need a `curl` cli tool to dowload `libuast`, and a `g++` for building [libtuast Python bindings](https://github.com/bblfsh/client-python/blob/0037d762563ab49b3daac8a7577f7103a5628fc6/setup.py#L17).
The command for Debian and derived distributions would be:

```bash
sudo apt install curl
sudo apt install build-essential
```

## Usage

A small example of how to parse a Python file and extract the import declarations from the [UAST](https://doc.bblf.sh/uast/uast-specification.html).

If you don't have a bblfsh server running you can execute it using the following command:

```sh
docker run --privileged --rm -it -p 9432:9432 -v bblfsh_cache:/var/lib/bblfshd --name bblfshd bblfsh/bblfshd
docker exec -it bblfshd bblfshctl driver install python bblfsh/python-driver:latest
```

Please, read the [getting started](https://doc.bblf.sh/using-babelfish/getting-started.html) guide to learn more about how to use and deploy a bblfshd.

```python
import bblfsh

client = bblfsh.BblfshClient("0.0.0.0:9432")
ctx = client.parse("/path/to/file.py")
print(ctx)
# or to get the results in a dictionary:
resdict = ctx.get_all()

# "filter' allows you to use XPath queries to filter on result nodes:
it = ctx.filter("//python:Call")
for node in it:
    print(node)
    # or:
    doSomething(node.get())

# filter must be used when using XPath functions returning these types:
# XPath queries can return different types (dicts, int, float, bool or str), 
# calling get() with an item will return the right type, but if you must ensure
# that you are getting the expected type (to avoid errors in the queries) there
# are alterative typed versions:
x = next(ctx.filter("boolean(//*[@strtOffset or @endOffset])").get_bool()
y = next(ctx.filter("name(//*[1])")).get_str()
z = next(ctx.filter("count(//*)").get_int() # or get_float()

# You can also iterate using iteration orders different than the 
# default preorder using the `iterate` method on `parse` result or node objects:

# Directly over parse results
it = client.parse("/path/to/file.py").iterate(bblfsh.TreeOrder.POST_ORDER)
for i in it: ...

# Over filter results (which by default are already iterators with PRE_ORDER):
ctx = client.parse("file.py")
newiter = ctx.filter("//python:Call").iterate(bblfsh.TreeOrder.LEVEL_ORDER)
for i in newiter: ...

# Over individual node objects to change the iteration order of
# a specific subtree:
ctx = client.parse("file.py")
first_node = next(ctx)
newiter = first_node.iterate(bblfsh.TreeOrder.POSITION_ORDER)
for i in newiter: ...

# You can also get the non semantic UAST or native AST:
ctx = client.parse("file.py", mode=bblfsh.ModeDict["NATIVE"])
# Possible values for ModeDict: DEFAULT_MODE, NATIVE, PREPROCESSED, ANNOTATED, SEMANTIC
```

Please read the [Babelfish clients](https://doc.bblf.sh/using-babelfish/clients.html)
guide section to learn more about babelfish clients and their query language.

## License

Apache License 2.0, see [LICENSE](LICENSE)
