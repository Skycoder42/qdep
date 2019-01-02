TEMPLATE = subdirs

SUBDIRS += tests

prepareRecursiveTarget(run-tests)
QMAKE_EXTRA_TARGETS += run-tests lrelease
