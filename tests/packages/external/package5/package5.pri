CONFIG += package5_included
DEFINES += PACKAGE5_DEFINED

QDEP_PACKAGE_EXPORTS += PACKAGE5_EXPORT
!qdep_build: DEFINES += "PACKAGE5_EXPORT="

QDEP_HOOK_FNS += dynamicclass_startup_hook

HEADERS += $$PWD/dynamicclass.h

SOURCES += $$PWD/dynamicclass.cpp

INCLUDEPATH += $$PWD
