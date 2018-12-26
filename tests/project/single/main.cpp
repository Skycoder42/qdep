#include <QCoreApplication>
#include <QtTest>
#include <iostream>

#include <simple.h>

int main(int argc, char **argv)
{
    QCoreApplication app{argc, argv};

    Simple simple;
    simple.value = "Hello World";
    QCOMPARE(simple.transform(), QString("hello world"));
    return 0;
}
