#!/bin/bash
set -e

$SUDO pip3 install appdirs lockfile argcomplete setuptools
$SUDO pip3 uninstall -y qdep

$SUDO pip3 install -e .
$SUDO qdep prfgen --qmake "/opt/qt/$QT_VER/$PLATFORM/bin/qmake"
