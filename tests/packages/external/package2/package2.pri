CONFIG += package2_included
DEFINES += PACKAGE2_DEFINED

QDEP_PACKAGE_EXPORTS += PACKAGE2_EXPORT
no_qdep: DEFINES += "PACKAGE2_EXPORT="

HEADERS += $$PWD/staticclass.h

SOURCES += $$PWD/staticclass.cpp

RESOURCES += $$PWD/package2.qrc

INCLUDEPATH += $$PWD
