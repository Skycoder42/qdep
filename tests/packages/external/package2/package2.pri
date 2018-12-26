CONFIG += package2_included
DEFINES += PACKAGE2_DEFINED

QDEP_EXPORTS += RANDOM_STRING
!qdep_build: DEFINES += PACKAGE2_EXPORT

HEADERS += $$PWD/staticclass.h

SOURCES += $$PWD/staticclass.cpp

INCLUDEPATH += $$PWD
