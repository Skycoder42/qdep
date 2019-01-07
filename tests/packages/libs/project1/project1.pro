TEMPLATE = lib
CONFIG += static

TARGET = project1

HEADERS += project1.h

SOURCES += project1.cpp

CONFIG += qdep_no_pull  # disable for performance - still enabled in first test
!load(qdep):error("Failed to load qdep feature")

QMAKE_EXTRA_TARGETS += run-tests
