CONFIG += package1_included
DEFINES += PACKAGE1_DEFINED

HEADERS += \
    $$PWD/simple.h

SOURCES += \
    $$PWD/simple.cpp

QDEP_TRANSLATIONS += \
    $$PWD/package2_de.ts \
    $$PWD/package2_en.ts \

INCLUDEPATH += $$PWD
