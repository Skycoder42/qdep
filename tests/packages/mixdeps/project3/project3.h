#ifndef PROJECT3_H
#define PROJECT3_H

#include <QtCore/QtGlobal>

#ifdef PROJECT3_BUILD
#define PROJECT3_EXPORT Q_DECL_EXPORT
#else
#define PROJECT3_EXPORT Q_DECL_IMPORT
#endif

namespace Project3 {

PROJECT3_EXPORT void doStuff();

}

#endif
