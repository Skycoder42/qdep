TEMPLATE = lib

TARGET = project2

HEADERS += project2.h

SOURCES += project2.cpp

QDEP_DEPENDS += Skycoder42/qdep@master/tests/packages/basic/package1/package1.pri
QDEP_PROJECT_DEPENDS += Skycoder42/qdep@master/tests/packages/libs/project3/project3.pro

CONFIG += qdep_no_pull  # disable for performance - still enabled in first test
!load(qdep):error("Failed to load qdep feature")

qdep_build:!package1_included: error("!package1_included")

# qdep stats
message("TARGET: $$TARGET")
!qdep_build:error("qdep was loaded, but qdep_build config is not set")
!isEmpty(__QDEP_REAL_DEPS_STACK):error("__QDEP_REAL_DEPS_STACK not empty: $$__QDEP_REAL_DEPS_STACK")
message("__QDEP_INCLUDE_CACHE:")
for(hash, __QDEP_INCLUDE_CACHE) {
    message("    $${hash}.package: $$eval($${hash}.package)")
    message("    $${hash}.version: $$eval($${hash}.version)")
    message("    $${hash}.path: $$eval($${hash}.path)")
    message("    $${hash}.exports: $$eval($${hash}.exports)")
    message("    $${hash}.local: $$eval($${hash}.local)")
    message("    $${hash}.target: $$eval($${hash}.target)")
    message("    $${hash}.file: $$eval($${hash}.file)")
    message("    $${hash}.depends: $$eval($${hash}.depends)")
}
message("QDEP_DEFINES: $$QDEP_DEFINES")
message("DEFINES: $$DEFINES")
message("QDEP_INCLUDEPATH: $$QDEP_INCLUDEPATH")
message("INCLUDEPATH: $$INCLUDEPATH")
message("__QDEP_PRIVATE_VARS_EXPORT: $$__QDEP_PRIVATE_VARS_EXPORT")
