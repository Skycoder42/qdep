TEMPLATE = subdirs

QDEP_PROJECT_DEPENDS += Skycoder42/qdep@master/tests/packages/libs/project1/project1.pro
QDEP_PROJECT_DEPENDS += Skycoder42/qdep@master/tests/packages/libs/project2/project2.pro

SUBDIRS += app

app.qdep_depends += Skycoder42/qdep@master/tests/packages/libs/project2/project2.pro

CONFIG += qdep_no_pull  # disable for performance - still enabled in first test
!load(qdep):error("Failed to load qdep feature")

CONFIG += no_run_tests_target
run-tests.target = run-tests
run-tests.CONFIG = recursive
run-tests.recurse_target = run-tests
run-tests.recurse += sub-app
include(../testrun.pri)

message($$SUBDIRS)
