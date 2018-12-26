#ifndef LIBDYNAMIC_H
#define LIBDYNAMIC_H

#include <QtGlobal>
#include <dynamicclass.h>

#ifdef LIBDYNAMIC_BUILD
#define LIBDYNAMIC_EXPORT Q_DECL_EXPORT
#else
#define LIBDYNAMIC_EXPORT Q_DECL_IMPORT
#endif

class LIBDYNAMIC_EXPORT LibDynamic : public DynamicClass
{
    double magicFraction();
};

#endif