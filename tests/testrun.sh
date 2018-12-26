#!/usr/bin/env bash
# $1 build path
# $2 qmake path
set -e

SCRIPT_PATH="$(readlink -f "$(dirname "$0")")"
BUILD_PATH="$1"
QMAKE="${2:-qmake}"

"$SCRIPT_PATH/../qdep.py" prfgen --qmake "$QMAKE"

mkdir -p "$BUILD_PATH"
cd "$BUILD_PATH"
"$QMAKE" "$SCRIPT_PATH/project/"
make qmake_all > /dev/null
make > /dev/null
make run-tests > /dev/null
