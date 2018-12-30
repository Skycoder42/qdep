TEMPLATE = subdirs

SUBDIRS += tests

prepareRecursiveTarget(lrelease)
prepareRecursiveTarget(run-tests)
QMAKE_EXTRA_TARGETS += run-tests lrelease
