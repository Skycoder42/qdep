TEMPLATE = subdirs

QDEP_PROJECT_DEPENDS += Skycoder42/qdep@master/tests/packages/libs/project1/project1.pro

SUBDIRS += app

app.qdep_depends += Skycoder42/qdep@master/tests/packages/libs/project1/project1.pro

CONFIG += qdep_no_pull  # disable for performance - still enabled in first test
!load(qdep):error("Failed to load qdep feature")

prepareRecursiveTarget(run-tests)
QMAKE_EXTRA_TARGETS += run-tests
