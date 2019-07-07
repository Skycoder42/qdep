TEMPLATE = subdirs

QDEP_PROJECT_SUBDIRS += Skycoder42/qdep@master/tests/packages/mixdeps/project1/project1.pro
QDEP_PROJECT_SUBDIRS += Skycoder42/qdep@master/tests/packages/mixdeps/project3/project3.pro
QDEP_PROJECT_SUBDIRS += Skycoder42/qdep@master/tests/packages/mixdeps/project4/project4.pro
QDEP_PROJECT_SUBDIRS += Skycoder42/qdep@master/tests/packages/mixdeps/project5/project5.pro

SUBDIRS += lib1 lib2 lib3 app

lib1.qdep_depends += Skycoder42/qdep@master/tests/packages/mixdeps/project1/project1.pro
lib1.qdep_depends += Skycoder42/qdep@master/tests/packages/mixdeps/project3/project3.pro
lib2.depends += lib3
lib2.qdep_depends += Skycoder42/qdep@master/tests/packages/mixdeps/project4/project4.pro
lib2.qdep_depends += Skycoder42/qdep@master/tests/packages/mixdeps/project5/project5.pro
app.depends += lib1 lib2

CONFIG += qdep_no_pull  # disable for performance - still enabled in first test
!load(qdep):error("Failed to load qdep feature")

CONFIG += no_run_tests_target
prepareRecursiveTarget(run-tests)
include(../testrun.pri)

message($$SUBDIRS)

# Project dependency structure:
#	app
#	|--lib1(s)
#	|	|--project1(s)
#	|	|	|--project2(s)
#	|	|--project3(d)
#	|--lib2(d)
#	|	|--lib3(s)
#	|	|--project4(s)
#	|	|--project5(d)
#	|	|	|--project3(d)
