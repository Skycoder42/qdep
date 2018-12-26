TEMPLATE = subdirs

SUBDIRS += \
    libstatic \
    libdynamic \
    app

prepareRecursiveTarget(run-tests)
QMAKE_EXTRA_TARGETS += run-tests
