TEMPLATE = app

SOURCES += \
    main.cpp

!load(qdep):error("Failed to load qdep feature")

QDEP_DEPENDS += Skycoder42/qdep@master/tests/package1/package1.pri

!qdep_include($$QDEP_DEPENDS):error("Failed to resolve qdep dependencies")
