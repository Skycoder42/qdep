TEMPLATE = app

SOURCES += \
    main.cpp

#CONFIG += qdep_no_qm_combine

#REPO_BASE = file:///home/sky/Programming/QtLibraries/qdep/.git
REPO_BASE = Skycoder42/qdep

QDEP_DEPENDS += $${REPO_BASE}@master/tests/packages/basic/package1/package1.pri

TRANSLATIONS += \
    single_de.ts \
    single_ja.ts

debug_and_release:CONFIG(release, debug|release): DEFINES += "\"TS_DIR=\\\"$$OUT_PWD/release\\\"\""
else:debug_and_release:CONFIG(debug, debug|release): DEFINES += "\"TS_DIR=\\\"$$OUT_PWD/debug\\\"\""
else: DEFINES += "\"TS_DIR=\\\"$$OUT_PWD\\\"\""

force_ts|CONFIG(release, debug|release): DEFINES += WITH_TRANSLATIONS

qdep_ts_target.path = $$[QT_INSTALL_TRANSLATIONS]
INSTALLS += qdep_ts_target

!load(qdep):error("Failed to load qdep feature")

include(../testrun.pri)

!package1_included: error("!package1_included")
