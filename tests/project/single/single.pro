TEMPLATE = app

CONFIG += lrelease

SOURCES += \
    main.cpp

#CONFIG += qdep_no_qm_combine

#REPO_BASE = file:///home/sky/Programming/QtLibraries/qdep/.git
REPO_BASE = Skycoder42/qdep

QDEP_DEPENDS += $${REPO_BASE}@master/tests/packages/basic/package1/package1.pri

TRANSLATIONS += \
    single_de.ts \
    single_ja.ts

DEFINES += "\"TS_DIR=\\\"$$absolute_path($$LRELEASE_DIR, $$OUT_PWD)\\\"\""

force_ts|CONFIG(release, debug|release): DEFINES += WITH_TRANSLATIONS

QM_FILES_INSTALL_PATH = $$[QT_INSTALL_TRANSLATIONS]

!load(qdep):error("Failed to load qdep feature")

include(../testrun.pri)

!package1_included: error("!package1_included")
