#!/bin/bash
set -e

$SUDO pip install appdirs lockfile
$SUDO ./qdep.py prfgen --qmake "/opt/qt/$QT_VER/$PLATFORM/bin/qmake"
mv tests/qdep.pro ./
