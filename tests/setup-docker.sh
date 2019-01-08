#!/bin/bash
set -e

$SUDO pip3 install appdirs lockfile argcomplete
$SUDO ./qdep.py prfgen --qmake "/opt/qt/$QT_VER/$PLATFORM/bin/qmake"
mv tests/qdep.pro ./
