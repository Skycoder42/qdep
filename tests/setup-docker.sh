#!/bin/bash
set -e

# install dependencies
$SUDO pip3 install appdirs lockfile argcomplete setuptools
$SUDO pip3 uninstall -y qdep

# install/prepare qdep
$SUDO pip3 install -e .
$SUDO qdep prfgen --qmake "/opt/qt/$QT_VER/$PLATFORM/bin/qmake"

# move project file
mv tests/qdep.pro ./
