#!/bin/bash
set -e

$SUDO pip3 install appdirs lockfile argcomplete setuptools
if pip3 list | grep qdep; then
	$SUDO pip3 uninstall qdep
fi

$SUDO pip3 install -e .
$SUDO qdep prfgen --qmake "/opt/qt/$QT_VER/$PLATFORM/bin/qmake"
