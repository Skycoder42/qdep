TEMPLATE = app

SOURCES += \
    main.cpp

QDEP_DEPENDS += Skycoder42/qdep@master/tests/package1/package1.pri
QDEP_DEPENDS += Skycoder42/qdep@master/tests/package2/package2.pri
QDEP_DEPENDS += Skycoder42/qdep@master/tests/package1/package1.pri
#QDEP_DEPENDS += Skycoder42/KeepassTransfer

!load(qdep):error("Failed to load qdep feature")

message("__QDEP_REAL_DEPS_STACK: $$__QDEP_REAL_DEPS_STACK")
message("__QDEP_INCLUDE_CACHE: $$__QDEP_INCLUDE_CACHE")
message("__QDEP_REAL_DEPS: $$__QDEP_REAL_DEPS")