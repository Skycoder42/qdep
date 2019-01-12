#!/bin/bash
set -e

$SUDO pip3 install appdirs lockfile argcomplete
mv tests/qdep.pro ./

$SUDO pip3 install -e .
$SUDO qdep prfgen --qmake "/opt/qt/$QT_VER/$PLATFORM/bin/qmake"
