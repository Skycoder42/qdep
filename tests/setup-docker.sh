#!/bin/bash
set -e

if [[ $TRAVIS_OS_NAME == "linux" ]]; then
	PIP=pip3
else
	PIP=pip
fi

$SUDO $PIP install appdirs lockfile
$SUDO ./qdep.py prfgen --qmake "/opt/qt/$QT_VER/$PLATFORM/bin/qmake"
mv tests/qdep.pro ./
