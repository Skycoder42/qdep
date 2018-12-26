TEMPLATE = subdirs

SUBDIRS += basic

prepareRecursiveTarget(run-tests)
QMAKE_EXTRA_TARGETS += run-tests