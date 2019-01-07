#ifndef PROJECT2_H
#define PROJECT2_H

#include <QtCore/QtGlobal>

#ifdef PROJECT2_BUILD
#define PROJECT2_EXPORT Q_DECL_EXPORT
#else
#define PROJECT2_EXPORT Q_DECL_IMPORT
#endif

namespace Project2 {

void PROJECT2_EXPORT doStuff();

}

#endif