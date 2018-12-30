TEMPLATE = subdirs

CONFIG += ordered

SUBDIRS += \
    single \
    basic \
    external

prepareRecursiveTarget(lrelease)
prepareRecursiveTarget(run-tests)
QMAKE_EXTRA_TARGETS += lrelease run-tests
