TEMPLATE = app

SOURCES += \
    main.cpp

!load(qdep):error("Failed to load qdep feature")

QDEP_DEPENDS += Skycoder42/qdep@master/tests/package1/package1.pri
#QDEP_DEPENDS += Skycoder42/qdep@master/tests/package1/package2.pri
#QDEP_DEPENDS += Skycoder42/KeepassTransfer

!qdep_include($$QDEP_DEPENDS):error("Failed to resolve qdep dependencies")

message(__QDEP_INCLUDE_CACHE $$__QDEP_INCLUDE_CACHE)