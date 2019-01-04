TEMPLATE = subdirs

CONFIG += ordered

SUBDIRS += \
    single \
    basic \
    external \
    libs

prepareRecursiveTarget(run-tests)
QMAKE_EXTRA_TARGETS += run-tests lrelease
