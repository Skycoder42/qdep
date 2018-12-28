#include "dynamicclass.h"
#include <QCoreApplication>

namespace {

bool _startup_run4 = false;

}

void dynamicclass_startup_hook()
{
    _startup_run4 = true;
}

#ifndef QDEP_BUILD
Q_COREAPP_STARTUP_FUNCTION(dynamicclass_startup_hook)
#endif

bool DynamicClass::startupRun()
{
    return _startup_run4;
}

int DynamicClass::magicNumber()
{
    return 425;
}
