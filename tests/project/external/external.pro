TEMPLATE = subdirs

SUBDIRS += \
    libstatic \
    libdynamic \
    app

app.depends += libstatic libdynamic

prepareRecursiveTarget(run-tests)
QMAKE_EXTRA_TARGETS += run-tests
