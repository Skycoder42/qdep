#!/bin/bash
set -e

SCRIPT_PATH="$(readlink -f "$(dirname "$0")")"

./qdep.py prfgen --qmake "$(which qmake)"

mv tests/qdep.pro ./
