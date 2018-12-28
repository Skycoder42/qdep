#include "staticclass.h"
#include <QCoreApplication>

namespace {

bool _startup_run = false;

}

void libstatic_startup_hook()
{
    _startup_run = true;
}

#ifndef QDEP_BUILD
Q_COREAPP_STARTUP_FUNCTION(libstatic_startup_hook)
#endif

bool StaticClass::startupRun()
{
    return _startup_run;
}

int StaticClass::magicNumber()
{
    return 422;
}
