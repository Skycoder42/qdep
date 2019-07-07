TEMPLATE = lib

TARGET = project5

HEADERS += project5.h

SOURCES += project5.cpp

QDEP_PROJECT_DEPENDS += Skycoder42/qdep@master/tests/packages/mixdeps/project3/project3.pro

CONFIG += qdep_no_pull  # disable for performance - still enabled in first test
!load(qdep):error("Failed to load qdep feature")

QMAKE_EXTRA_TARGETS += run-tests
