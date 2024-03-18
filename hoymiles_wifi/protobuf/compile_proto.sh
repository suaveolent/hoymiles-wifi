#!/bin/bash

for file in $(ls *.proto)
do
  #protoc --pyi_out=. $file
  protoc --python_out=. $file
done
