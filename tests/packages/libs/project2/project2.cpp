#include "project2.h"
#include <simple.h>
#include <project3.h>

void Project2::doStuff()
{
    Simple simple;
    simple.value = QStringLiteral("BAUM42");
    simple.transform();
    Project3::doStuff();
}
