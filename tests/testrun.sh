#!/usr/bin/env bash
# $1 build path
# $2 qmake path
# $3 test commands only
set -ex

SCRIPT_PATH="$(readlink -f "$(dirname "$0")")"
TEST_PATH="$1"
BUILD_PATH="$1/project"
CMD_PATH="$1/cmd"
QMAKE="${2:-qmake}"
COMMANDS="$3"

export PYTHONPATH="$(realpath "$SCRIPT_PATH/.."):$PYTHONPATH"

"$SCRIPT_PATH/testentry.py" prfgen --qmake "$QMAKE"

mkdir -p "$TEST_PATH/testgitroot/Skycoder42"
if [ ! -e "$TEST_PATH/testgitroot/Skycoder42/qdep" ]; then
    ln -s "$(realpath "$SCRIPT_PATH/..")" "$TEST_PATH/testgitroot/Skycoder42/qdep"
fi

if [ -z "$COMMANDS" ]; then
    mkdir -p "$BUILD_PATH"
    cd "$BUILD_PATH"
    "$QMAKE" "CONFIG+=local_test_run" "$SCRIPT_PATH/project/"
    make qmake_all
    make

    make INSTALL_ROOT="$BUILD_PATH/install" install
    [ -e "$BUILD_PATH/install$($QMAKE -query QT_INSTALL_TRANSLATIONS)/single_de.qm" ]
    [ -e "$BUILD_PATH/install$($QMAKE -query QT_INSTALL_TRANSLATIONS)/single_ja.qm" ]

    export LD_LIBRARY_PATH="$BUILD_PATH/external/libdynamic/:$LD_LIBRARY_PATH"
    make run-tests
else
    mkdir -p "$CMD_PATH"
    cd "$CMD_PATH"
    "$QMAKE" "CONFIG+=local_test_run" "$SCRIPT_PATH/project/commands"
    make run-tests
fi
