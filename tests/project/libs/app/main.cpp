#include <QCoreApplication>
#include <tests.h>
#include <project2.h>

int main(int argc, char **argv)
{
    QCoreApplication app{argc, argv};
    Project2::doStuff();

    return 0;
}
