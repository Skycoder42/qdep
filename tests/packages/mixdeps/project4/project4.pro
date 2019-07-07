TEMPLATE = lib
CONFIG += static

TARGET = project4

HEADERS += project4.h

SOURCES += project4.cpp

QDEP_DEFINES += PROJECT4_DEFINED

CONFIG += qdep_no_pull  # disable for performance - still enabled in first test
!load(qdep):error("Failed to load qdep feature")

QMAKE_EXTRA_TARGETS += run-tests
