TEMPLATE = lib

QDEP_DEPENDS += Skycoder42/qdep@master/tests/packages/external/package2/package2.pri
QDEP_DEPENDS += Skycoder42/qdep@master/tests/packages/external/package3/package3.pri

!load(qdep):error("Failed to load qdep feature")

!package2_included: error("!package2_included")
!package3_included: error("!package3_included")

QMAKE_EXTRA_TARGETS += run-tests