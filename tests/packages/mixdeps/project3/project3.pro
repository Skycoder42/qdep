TEMPLATE = lib

TARGET = project3

HEADERS += project3.h

SOURCES += project3.cpp

DEFINES += PROJECT3_BUILD

CONFIG += qdep_no_pull  # disable for performance - still enabled in first test
!load(qdep):error("Failed to load qdep feature")

QMAKE_EXTRA_TARGETS += run-tests
