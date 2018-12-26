#!/bin/bash
set -e

SCRIPT_PATH="$(readlink -f "$(dirname "$0")")"

./qdep.py prfgen --qmake "/opt/qt/$QT_VER/$PLATFORM/bin/qmake"

mv tests/qdep.pro ./
