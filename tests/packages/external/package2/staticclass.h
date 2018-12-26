#ifndef STATICCLASS_H
#define STATICCLASS_H

#ifdef PACKAGE2_EXPORT
#error PACKAGE2_EXPORT
#endif

class PACKAGE2_EXPORT StaticClass
{
    int magicNumber();
};

#endif