TEMPLATE = subdirs

CONFIG += ordered

SUBDIRS += \
    single \
    basic

prepareRecursiveTarget(run-tests)
QMAKE_EXTRA_TARGETS += run-tests