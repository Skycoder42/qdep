#ifndef PROJECT5_H
#define PROJECT5_H

#include <QtCore/QtGlobal>

#ifdef PROJECT5_BUILD
#define PROJECT5_EXPORT Q_DECL_EXPORT
#else
#define PROJECT5_EXPORT Q_DECL_IMPORT
#endif

namespace Project5 {

PROJECT5_EXPORT void doStuff();

}

#endif
