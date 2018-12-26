TEMPLATE = lib

QDEP_DEPENDS += Skycoder42/qdep@master/tests/packages/external/package4/package4.pri
QDEP_DEPENDS += Skycoder42/qdep@master/tests/packages/external/package5/package5.pri

!load(qdep):error("Failed to load qdep feature")

!package4_included: error("!package4_included")
!package5_included: error("!package5_included")

QMAKE_EXTRA_TARGETS += run-tests
