CONFIG += package2_included
DEFINES += PACKAGE2_DEFINED

QDEP_EXPORTS += PACKAGE2_EXPORT
!qdep_build: DEFINES += "PACKAGE2_EXPORT="

HEADERS += $$PWD/staticclass.h

SOURCES += $$PWD/staticclass.cpp

INCLUDEPATH += $$PWD
