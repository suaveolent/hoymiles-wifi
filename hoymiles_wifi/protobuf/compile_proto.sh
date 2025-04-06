#!/bin/bash

# wget https://github.com/protocolbuffers/protobuf/releases/download/v30.2/protoc-30.2-linux-x86_64.zip

for file in $(ls *.proto)
do
  #protoc --pyi_out=. $file
  protoc --python_out=. $file
done
