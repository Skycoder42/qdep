TEMPLATE = lib
CONFIG += static

QT += sql

TARGET = lib3

HEADERS += lib3.h

SOURCES += lib3.cpp

QDEP_DEFINES += LIB3_DEFINED

CONFIG += qdep_no_pull  # disable for performance - still enabled in first test
!load(qdep):error("Failed to load qdep feature")

CONFIG += no_run_tests_target
include(../../testrun.pri)

message(LIBS: $$LIBS)
