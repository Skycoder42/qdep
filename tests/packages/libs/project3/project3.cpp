#include "project3.h"
#include <simple.h>

void Project3::doStuff()
{
    Simple simple;
    simple.value = QStringLiteral("TREE42");
    simple.transform();
}
