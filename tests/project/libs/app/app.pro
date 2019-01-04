TEMPLATE = app

QDEP_PROJECT_DEPENDS += Skycoder42/qdep@master/tests/packages/libs/project2/project2.pro

SOURCES += main.cpp

CONFIG += qdep_no_pull  # disable for performance - still enabled in first test
!load(qdep):error("Failed to load qdep feature")

include(../../testrun.pri)
