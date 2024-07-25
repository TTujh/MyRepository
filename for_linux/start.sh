#!/bin/bash

x=$(dirname $(find $(pwd) -name start.sh))
cd $x
while true; do ./CodeGeneratorRun; done
