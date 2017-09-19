PYTHON ?= python3

makefile_dir := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

LIBUAST_VERSION = v0.2.1
SDK_VERSION = v0

.PHONY : all clean deps

all: deps \
	bblfsh/github/com/gogo/protobuf/gogoproto/gogo_pb2.py \
	bblfsh/gopkg/in/bblfsh/sdk/$(SDK_VERSION)/uast/generated_pb2.py \
	bblfsh/gopkg/in/bblfsh/sdk/$(SDK_VERSION)/protocol/generated_pb2_*.py \
	bblfsh/github/__init__.py \
	bblfsh/github/com/__init__.py \
	bblfsh/github/com/gogo/__init__.py \
	bblfsh/github/com/gogo/protobuf/__init__.py \
	bblfsh/github/com/gogo/protobuf/gogoproto/__init__.py \
	bblfsh/gopkg/__init__.py \
	bblfsh/gopkg/in/__init__.py \
	bblfsh/gopkg/in/bblfsh/__init__.py \
	bblfsh/gopkg/in/bblfsh/sdk/__init__.py \
	bblfsh/gopkg/in/bblfsh/sdk/$(SDK_VERSION)/__init__.py \
	bblfsh/gopkg/in/bblfsh/sdk/$(SDK_VERSION)/uast/__init__.py \
	bblfsh/gopkg/in/bblfsh/sdk/$(SDK_VERSION)/protocol/__init__.py

clean:
	rm -rf bblfsh/libuast
	rm -rf bblfsh/github
	rm -rf bblfsh/gopkg

deps: bblfsh/libuast

bblfsh/libuast:
	curl -SL https://github.com/bblfsh/libuast/releases/download/$(LIBUAST_VERSION)/libuast-$(LIBUAST_VERSION).tar.gz | tar xz
	mv libuast-$(LIBUAST_VERSION) libuast
	cp -a libuast/src bblfsh/libuast
	rm -rf libuast

bblfsh/github/com/gogo/protobuf/gogoproto/gogo_pb2.py: github.com/gogo/protobuf/gogoproto/gogo.proto
	protoc --python_out bblfsh github.com/gogo/protobuf/gogoproto/gogo.proto

bblfsh/gopkg/in/bblfsh/sdk/$(SDK_VERSION)/uast/generated_pb2.py: gopkg.in/bblfsh/sdk.$(SDK_VERSION)/uast/generated.proto
	protoc --python_out bblfsh gopkg.in/bblfsh/sdk.$(SDK_VERSION)/uast/generated.proto

bblfsh/gopkg/in/bblfsh/sdk/$(SDK_VERSION)/protocol:
	@mkdir -p $@

bblfsh/gopkg/in/bblfsh/sdk/$(SDK_VERSION)/uast:
	@mkdir -p $@

bblfsh/github/com/gogo/protobuf/gogoproto:
	@mkdir -p $@

bblfsh/gopkg/in/bblfsh/sdk/$(SDK_VERSION)/protocol/generated_pb2_*.py: \
	bblfsh/gopkg/in/bblfsh/sdk/$(SDK_VERSION)/protocol gopkg.in/bblfsh/sdk.$(SDK_VERSION)/protocol/generated.proto
	$(PYTHON) -m grpc.tools.protoc --python_out=bblfsh/gopkg/in/bblfsh/sdk/$(SDK_VERSION)/protocol \
	    --grpc_python_out=bblfsh/gopkg/in/bblfsh/sdk/$(SDK_VERSION)/protocol \
	    -I gopkg.in/bblfsh/sdk.$(SDK_VERSION)/protocol -I $(makefile_dir) \
	    gopkg.in/bblfsh/sdk.$(SDK_VERSION)/protocol/generated.proto

%/__init__.py:
	@touch $@
