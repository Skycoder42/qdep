CONFIG += package5_included
DEFINES += PACKAGE5_DEFINED

QDEP_PACKAGE_EXPORTS += PACKAGE5_EXPORT
no_qdep: DEFINES += "PACKAGE5_EXPORT="

HEADERS += $$PWD/dynamicclass.h

SOURCES += $$PWD/dynamicclass.cpp

INCLUDEPATH += $$PWD
