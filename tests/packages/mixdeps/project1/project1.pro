TEMPLATE = lib
CONFIG += static

TARGET = project1

HEADERS += project1.h

SOURCES += project1.cpp

QDEP_PROJECT_DEPENDS += Skycoder42/qdep@master/tests/packages/mixdeps/project2/project2.pro

CONFIG += qdep_no_pull  # disable for performance - still enabled in first test
!load(qdep):error("Failed to load qdep feature")

qdeb_build:!contains(DEFINES, PROJECT2_DEFINED): error("!PROJECT2_DEFINED")

QMAKE_EXTRA_TARGETS += run-tests
