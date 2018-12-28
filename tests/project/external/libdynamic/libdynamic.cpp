#include "libdynamic.h"

namespace {

bool _startup_run3 = false;

}

void libdynamic_startup_hook()
{
    _startup_run3 = true;
}

bool LibDynamic::libStartupRun()
{
    return _startup_run3;
}

double LibDynamic::magicFraction()
{
    return 0.24;
}
