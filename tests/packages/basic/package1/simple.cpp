#include "simple.h"

QString Simple::transform() const
{
    return value.toLower();
}

QString Simple::translate() const
{
    return tr("Hello World");
}
