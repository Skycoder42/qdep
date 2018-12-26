#include <QCoreApplication>
#include <iostream>

#include <simple.h>

int main(int argc, char **argv)
{
    QCoreApplication app{argc, argv};

    Simple simple;
    simple.value = "Hello World";
    std::cout << simple.transform().toStdString() << std::endl;
    return 0;
}
