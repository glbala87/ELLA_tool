#!/bin/bash

set -e # exit on first failure
mypy /ella/src/api/main.py

echo "mypy successfully completed"
