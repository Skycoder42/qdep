#!/usr/bin/env bash
# $1 build path
# $2 qmake path
set -ex

SCRIPT_PATH="$(readlink -f "$(dirname "$0")")"
BUILD_PATH="$1"
QMAKE="${2:-qmake}"

"$SCRIPT_PATH/../qdep.py" prfgen --qmake "$QMAKE"

mkdir -p "$BUILD_PATH/testgitroot/Skycoder42"
if [ ! -e "$BUILD_PATH/testgitroot/Skycoder42/qdep" ]; then
    ln -s "$(realpath "$SCRIPT_PATH/..")" "$BUILD_PATH/testgitroot/Skycoder42/qdep"
fi

mkdir -p "$BUILD_PATH"
cd "$BUILD_PATH"
"$QMAKE" "$SCRIPT_PATH/project/"
make qmake_all
make

make INSTALL_ROOT="$BUILD_PATH/install" install
[ -e "$BUILD_PATH/install$($QMAKE -query QT_INSTALL_TRANSLATIONS)/single_de.qm" ]
[ -e "$BUILD_PATH/install$($QMAKE -query QT_INSTALL_TRANSLATIONS)/single_ja.qm" ]

export LD_LIBRARY_PATH="$BUILD_PATH/external/libdynamic/:$LD_LIBRARY_PATH"
make run-tests
