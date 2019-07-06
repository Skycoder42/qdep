TEMPLATE = lib
CONFIG += static

TARGET = lib1

HEADERS += lib1.h

SOURCES += lib1.cpp

QDEP_PROJECT_ROOT = ..
QDEP_PROJECT_LINK_DEPENDS += Skycoder42/qdep@master/tests/packages/mixdeps/project1/project1.pro

CONFIG += qdep_no_pull  # disable for performance - still enabled in first test
!load(qdep):error("Failed to load qdep feature")

CONFIG += no_run_tests_target
include(../../testrun.pri)
