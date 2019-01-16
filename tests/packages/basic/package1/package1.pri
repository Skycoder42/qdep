CONFIG += package1_included
DEFINES += PACKAGE1_DEFINED

HEADERS += \
    $$PWD/simple.h

SOURCES += \
    $$PWD/simple.cpp

QDEP_TRANSLATIONS += \
    $$PWD/package1_de.ts \
    $$PWD/package1_en.ts \

INCLUDEPATH += $$PWD
