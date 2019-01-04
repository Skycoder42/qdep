#include "project2.h"
#include <simple.h>

Project2::doStuff()
{
    Simple simple;
    simple.value = QStringLiteral("BAUM42");
    simple.transform();
}
