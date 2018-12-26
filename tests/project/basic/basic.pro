TEMPLATE = app

SOURCES += \
    main.cpp

#REPO_BASE = file:///home/sky/Programming/QtLibraries/qdep/.git
REPO_BASE = Skycoder42/qdep

QDEP_DEPENDS += $${REPO_BASE}@master/tests/packages/basic/package1/package1.pri
QDEP_DEPENDS += $${REPO_BASE}@master/tests/packages/basic/package2/package2.pri
QDEP_DEPENDS += $${REPO_BASE}@master/tests/packages/basic/package1/package1.pri

CONFIG += qdep_no_pull  # disable for performance - still enabled in first test
!load(qdep):error("Failed to load qdep feature")

include(../testrun.pri)

!package1_included: error("!package1_included")
!package2_included: error("!package2_included")
!package3_included: error("!package3_included")
!package4_included: error("!package4_included")
!package5_included: error("!package5_included")
