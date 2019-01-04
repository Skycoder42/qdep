TEMPLATE = lib
CONFIG += static

TARGET = project1

HEADERS += libproject1.h

SOURCES += libproject1.cpp

CONFIG += qdep_no_pull  # disable for performance - still enabled in first test
!load(qdep):error("Failed to load qdep feature")
