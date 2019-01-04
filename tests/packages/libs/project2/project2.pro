TEMPLATE = lib

TARGET = project2

HEADERS += project2.h

SOURCES += project2.cpp

QDEP_DEPENDS += Skycoder42/qdep@master/tests/packages/basic/package1/package1.pri
QDEP_PROJECT_DEPENDS += Skycoder42/qdep@master/tests/packages/libs/project3/project3.pro

CONFIG += qdep_no_pull  # disable for performance - still enabled in first test
!load(qdep):error("Failed to load qdep feature")

qdep_build:!package1_included: error("!package1_included")
