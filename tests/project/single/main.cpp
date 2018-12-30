#include <QCoreApplication>
#include <QLocale>
#include <tests.h>

#include <simple.h>

int main(int argc, char **argv)
{
    QCoreApplication app{argc, argv};
    QLocale::setDefault(QLocale{QLocale::German, QLocale::Germany});

    Simple simple;
    simple.value = QCoreApplication::translate("GLOBAL", "Hello Tree");
    COMPARE(simple.transform(), QString("hello tree"));
    //COMPARE(simple.translate(), QString("Hallo Welt"));
    return 0;
}
