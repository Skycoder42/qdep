TEMPLATE = subdirs

CONFIG += ordered

SUBDIRS += \
	single \
	basic \
	external \
	libs \
	mixdeps \
	commands

prepareRecursiveTarget(run-tests)
QMAKE_EXTRA_TARGETS += run-tests lrelease
