## Babelfish Python client [![Build Status](https://travis-ci.org/bblfsh/client-python.svg?branch=master)](https://travis-ci.org/bblfsh/client-python)

This a pure Python implementation of querying [Babelfish](https://doc.bblf.sh/) server.

### Usage

API
```python
from bblfsh import BblfshClient, filter

client = BblfshClient("0.0.0.0:9432")
print(client.parse("/path/to/file.py"))
# "filter' allows you to use XPath queries to filter on result nodes:
print(client.filter("//Import[@roleImportDeclaration]//alias")
```

*TODO*: Link to `libuast` XPath documentation when available.

Command line
```bash
python3 -m bblfsh -f file.py
```

This will usually download and run a server Docker image automatically, but it'll
also use an existing image if it's previously running. You could run a bblfsh
server image with:

```bash
docker run --privileged -d -p 9432:9432 --name bblfsh bblfsh/server
```

### Installation

#### Dependencies

You need to install `libxml2` and its header files. The command for 
Debian and derived distributions would be:

```bash
sudo apt install libxml2-dev
```

#### From the source code

```bash
git clone https://github.com/bblfsh/client-python.git
cd client-python
make install
```

#### Using pip3

```bash
pip3 install bblfsh
```

It is possible to regenerate the gRPC/protobuf bindings by executing `make`.

### License

Apache 2.0.
