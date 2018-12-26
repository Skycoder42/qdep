TEMPLATE = app

SOURCES += \
    main.cpp

QDEP_DEPENDS += Skycoder42/qdep@master/tests/packages/external/package1/package1.pri

!load(qdep):error("Failed to load qdep feature")

include(../../testrun.pri)
