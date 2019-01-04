TEMPLATE = lib
CONFIG += static

TARGET = project3

HEADERS += project3.h

SOURCES += project3.cpp

QDEP_DEPENDS += Skycoder42/qdep@master/tests/packages/basic/package1/package1.pri
QDEP_EXPORTS += Skycoder42/qdep@master/tests/packages/basic/package1/package1.pri

CONFIG += qdep_no_pull  # disable for performance - still enabled in first test
!load(qdep):error("Failed to load qdep feature")

!package1_included: error("!package1_included")
