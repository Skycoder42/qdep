TEMPLATE = app

SOURCES += main.cpp

QDEP_LINK_DEPENDS += ../lib1

CONFIG += qdep_no_pull  # disable for performance - still enabled in first test
!load(qdep):error("Failed to load qdep feature")

include(../../testrun.pri)

message(LIBS: $$LIBS)
