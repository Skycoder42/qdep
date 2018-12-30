TEMPLATE = subdirs

SUBDIRS += project

prepareRecursiveTarget(lrelease)
prepareRecursiveTarget(run-tests)
QMAKE_EXTRA_TARGETS += run-tests lrelease
