TEMPLATE = app

SOURCES += \
    main.cpp

#REPO_BASE = file:///home/sky/Programming/QtLibraries/qdep/.git
REPO_BASE = Skycoder42/qdep

QDEP_DEPENDS += $${REPO_BASE}@master/tests/package1/package1.pri
QDEP_DEPENDS += $${REPO_BASE}@master/tests/package2/package2.pri
QDEP_DEPENDS += $${REPO_BASE}@master/tests/package1/package1.pri

!load(qdep):error("Failed to load qdep feature")

message("__QDEP_REAL_DEPS_STACK: $$__QDEP_REAL_DEPS_STACK")
message("__QDEP_REAL_DEPS: $$__QDEP_REAL_DEPS")
message("__QDEP_INCLUDE_CACHE:")
for(hash, __QDEP_INCLUDE_CACHE) {
    message("    $${hash}.package: $$first($${hash}.package)")
    message("    $${hash}.version: $$first($${hash}.version)")
}

!package1_included: error("!package1_included")
!package2_included: error("!package2_included")
!package3_included: error("!package3_included")
!package4_included: error("!package4_included")
!package5_included: error("!package5_included")

include(../testrun.pri)
