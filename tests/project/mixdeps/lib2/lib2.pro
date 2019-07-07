TEMPLATE = lib

TARGET = lib2

HEADERS += lib2.h

SOURCES += lib2.cpp

QDEP_LINK_DEPENDS += ../lib3

QDEP_PROJECT_ROOT = ..
QDEP_PROJECT_LINK_DEPENDS += Skycoder42/qdep@master/tests/packages/mixdeps/project4/project4.pro
QDEP_PROJECT_LINK_DEPENDS += Skycoder42/qdep@master/tests/packages/mixdeps/project5/project5.pro

CONFIG += qdep_no_pull  # disable for performance - still enabled in first test
!load(qdep):error("Failed to load qdep feature")

!contains(DEFINES, LIB3_DEFINED): error("!LIB3_DEFINED")
!contains(DEFINES, PROJECT4_DEFINED): error("!PROJECT4_DEFINED")
!contains(QT, sql): error("sql")

CONFIG += no_run_tests_target
include(../../testrun.pri)

message(LIBS: $$LIBS)
