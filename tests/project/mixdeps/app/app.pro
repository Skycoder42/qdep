TEMPLATE = app

SOURCES += main.cpp

QDEP_LINK_DEPENDS += ../lib1
# TODO remove again
QDEP_PROJECT_ROOT = ..
QDEP_PROJECT_LINK_DEPENDS += Skycoder42/qdep@master/tests/packages/mixdeps/project2/project2.pro

CONFIG += qdep_no_pull  # disable for performance - still enabled in first test
!load(qdep):error("Failed to load qdep feature")

include(../../testrun.pri)
