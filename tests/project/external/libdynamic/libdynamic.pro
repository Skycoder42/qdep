TEMPLATE = lib

TARGET = libdynamic

DEFINES += LIBDYNAMIC_BUILD

QDEP_DEPENDS += Skycoder42/qdep@master/tests/packages/external/package4/package4.pri
QDEP_DEPENDS += Skycoder42/qdep@master/tests/packages/external/package5/package5.pri

QDEP_HOOK_FNS += libdynamic_startup_hook

QDEP_DEFINES += LIBDYNAMIC_TEST
QDEP_INCLUDEPATH += $$PWD/extra

HEADERS += libdynamic.h

SOURCES += libdynamic.cpp

#CONFIG += qdep_export
CONFIG += qdep_export_all

CONFIG += qdep_no_pull  # disable for performance - still enabled in first test
!load(qdep):error("Failed to load qdep feature")

CONFIG += no_run_tests_target
include(../../testrun.pri)

!package4_included: error("!package4_included")
!package5_included: error("!package5_included")
