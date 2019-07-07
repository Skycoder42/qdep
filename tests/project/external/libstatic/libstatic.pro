TEMPLATE = lib
CONFIG += static

TARGET = super-static

debug_and_release:CONFIG(release, debug|release): DESTDIR = libout/release
else:debug_and_release:CONFIG(debug, debug|release):  DESTDIR = libout/debug
else: DESTDIR = libout

HEADERS += libstatic.h

SOURCES += libstatic.cpp

RESOURCES += \
	super-static.qrc

QDEP_DEPENDS += Skycoder42/qdep@master/tests/packages/external/package2/package2.pri
QDEP_DEPENDS += Skycoder42/qdep@master/tests/packages/external/package3/package3.pri

QDEP_HOOK_FNS += libstatic::hooks::startup_hook

QDEP_DEFINES += LIBSTATIC_TEST
QDEP_INCLUDEPATH += $$PWD/extra

QDEP_EXPORTS += Skycoder42/qdep@master/tests/packages/external/package2/package2.pri

CONFIG += qdep_link_private

CONFIG += qdep_no_pull  # disable for performance - still enabled in first test
!load(qdep):error("Failed to load qdep feature")

CONFIG += no_run_tests_target
include(../../testrun.pri)

!package2_included: error("!package2_included")
!package3_included: error("!package3_included")
