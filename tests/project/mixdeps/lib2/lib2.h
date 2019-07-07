#ifndef LIB2_H
#define LIB2_H

#include <QtCore/QtGlobal>

#ifdef LIB2_BUILD
#define LIB2_EXPORT Q_DECL_EXPORT
#else
#define LIB2_EXPORT Q_DECL_IMPORT
#endif

class LIB2_EXPORT Lib2
{
public:
	static void lib2();
};

#endif
