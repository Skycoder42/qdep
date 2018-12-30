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

DEFINES += "\"TS_DIR=\\\"$$OUT_PWD\\\"\""

!load(qdep):error("Failed to load qdep feature")

include(../testrun.pri)

!package1_included: error("!package1_included")
