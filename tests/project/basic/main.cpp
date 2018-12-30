#include <QCoreApplication>
#include <tests.h>

#include <simple.h>

int main(int argc, char **argv)
{
    QCoreApplication app{argc, argv};

    Simple simple;
    simple.value = QCoreApplication::translate("GLOBAL", "Hello Tree");
    COMPARE(simple.transform(), QStringLiteral("hello world"));
    return 0;
}
