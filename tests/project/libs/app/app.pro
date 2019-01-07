TEMPLATE = app

SOURCES += main.cpp

QDEP_PROJECT_ROOT = ..
# QDEP_PROJECT_ROOT = ../libs.pro
QDEP_PROJECT_LINK_DEPENDS += Skycoder42/qdep@master/tests/packages/libs/project2/project2.pro

CONFIG += qdep_no_pull  # disable for performance - still enabled in first test
!load(qdep):error("Failed to load qdep feature")

include(../../testrun.pri)
