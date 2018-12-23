#include "simple.h"

QString Simple::transform() const
{
    return value.toLower() + "X";
}
