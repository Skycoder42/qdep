TEMPLATE = lib
CONFIG += static

TARGET = project2

HEADERS += project2.h

SOURCES += project2.cpp

QDEP_DEFINES += PROJECT2_DEFINED

CONFIG += qdep_no_pull  # disable for performance - still enabled in first test
!load(qdep):error("Failed to load qdep feature")

QMAKE_EXTRA_TARGETS += run-tests
