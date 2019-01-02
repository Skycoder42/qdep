TEMPLATE = subdirs

SUBDIRS += project

prepareRecursiveTarget(run-tests)
QMAKE_EXTRA_TARGETS += run-tests
