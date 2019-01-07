TEMPLATE = lib

TARGET = project2

HEADERS += project2.h

SOURCES += project2.cpp

DEFINES += PROJECT2_BUILD

QDEP_DEPENDS += Skycoder42/qdep@master/tests/packages/basic/package1/package1.pri  # provided via project3
QDEP_PROJECT_DEPENDS += Skycoder42/qdep@master/tests/packages/libs/project3/project3.pro

CONFIG += qdep_no_pull  # disable for performance - still enabled in first test
!load(qdep):error("Failed to load qdep feature")

qdep_build:package1_included: error("package1_included")
qdeb_build:contains(DEFINES, PACKAGE1_DEFINED): error("!PACKAGE1_DEFINED")

QMAKE_EXTRA_TARGETS += run-tests
