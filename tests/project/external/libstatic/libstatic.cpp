#include "libstatic.h"

namespace {

bool _startup_run2 = false;

}

namespace libstatic::hooks {

void startup_hook()
{
	_startup_run2 = true;
}

}

bool LibStatic::libStartupRun()
{
	return _startup_run2;
}

double LibStatic::magicFraction()
{
	return 0.42;
}
