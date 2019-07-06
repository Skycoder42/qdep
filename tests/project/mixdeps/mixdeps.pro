TEMPLATE = subdirs

QDEP_PROJECT_SUBDIRS += Skycoder42/qdep@master/tests/packages/mixdeps/project1/project1.pro

SUBDIRS += lib1 app

lib1.qdep_depends += Skycoder42/qdep@master/tests/packages/mixdeps/project1/project1.pro
app.depends += lib1

CONFIG += qdep_no_pull  # disable for performance - still enabled in first test
!load(qdep):error("Failed to load qdep feature")

CONFIG += no_run_tests_target
prepareRecursiveTarget(run-tests)
include(../testrun.pri)

message($$SUBDIRS)
