#ifndef LIBSTATIC_H
#define LIBSTATIC_H

#include <staticclass.h>

class LibStatic : public StaticClass
{
public:
    static bool libStartupRun();

    double magicFraction();
};

#endif