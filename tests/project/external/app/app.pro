TEMPLATE = app

SOURCES += \
    main.cpp

QDEP_DEPENDS += Skycoder42/qdep@master/tests/packages/external/package1/package1.pri
QDEP_DEPENDS += Skycoder42/qdep@master/tests/packages/external/package3/package3.pri
QDEP_DEPENDS += Skycoder42/qdep@master/tests/packages/external/package5/package5.pri

QDEP_HOOK_FNS += app_startup_hook

QDEP_LINK_DEPENDS += ../libstatic/libstatic.pro $$OUT_PWD/../libdynamic
#CONFIG += qdep_no_link

CONFIG += qdep_no_pull  # disable for performance - still enabled in first test
!load(qdep):error("Failed to load qdep feature")

include(../../testrun.pri)

!package1_included: error("!package1_included")
package2_included: error("package2_included")
package3_included: error("package3_included")
package4_included: error("package4_included")
package5_included: error("package5_included")

!contains(DEFINES, PACKAGE1_DEFINED):error("!PACKAGE1_DEFINED")
!contains(DEFINES, PACKAGE2_DEFINED):error("!PACKAGE2_DEFINED")
contains(DEFINES, PACKAGE3_DEFINED):error("PACKAGE3_DEFINED")
!contains(DEFINES, PACKAGE4_DEFINED):error("!PACKAGE4_DEFINED")
!contains(DEFINES, PACKAGE5_DEFINED):error("!PACKAGE5_DEFINED")

!contains(FUNNY_STUFF, baum42):error("QDEP_VAR_EXPORTS failed")
!contains(FUNNY_STUFF, baum24):error("QDEP_VAR_EXPORTS failed")
