TEMPLATE = app

SOURCES += main.cpp

QDEP_LINK_DEPENDS += ../lib1 ../lib2

CONFIG += qdep_no_pull  # disable for performance - still enabled in first test
!load(qdep):error("Failed to load qdep feature")

!contains(DEFINES, LIB3_DEFINED): error("!LIB3_DEFINED")
!contains(DEFINES, PROJECT4_DEFINED): error("!PROJECT4_DEFINED")
!contains(QT, sql): error("sql")
contains(LIBS, -llib3): error("-llib3")
contains(LIBS, -lproject4): error("-lproject4")

include(../../testrun.pri)

message(LIBS: $$LIBS)
