## Babelfish Python client [![Build Status](https://travis-ci.org/bblfsh/client-python.svg?branch=master)](https://travis-ci.org/bblfsh/client-python)

This a pure Python implementation of querying [Babelfish](https://doc.bblf.sh/) server.

### Usage

API
```
from bblfsh import BblfshClient

client = BblfshClient("0.0.0.0:9432")
print(client.parse("/path/to/file.py"))
```

Command line
```
python3 -m bblfsh -f file.py
```

### Installation

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
