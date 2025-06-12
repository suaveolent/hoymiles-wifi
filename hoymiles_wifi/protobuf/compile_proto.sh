#!/bin/bash

for file in $(ls *.proto)
do
  protoc --python_out=. $file
done
