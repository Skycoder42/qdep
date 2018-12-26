#!/bin/bash
set -e

$SUDO ./qdep.py prfgen --qmake "/opt/qt/$QT_VER/$PLATFORM/bin/qmake"
mv tests/qdep.pro ./
