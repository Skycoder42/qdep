#include <QCoreApplication>
#include <QFile>
#include <tests.h>

#include <libstatic.h>
#include <libdynamic.h>

#include <extra_sta.h>
#include <extra_dyn.h>

namespace {
bool startuped = false;
}

void app_startup_hook()
{
    startuped = true;
}

int main(int argc, char **argv)
{
    QCoreApplication app{argc, argv};

    VERIFY(StaticClass::startupRun());
    VERIFY(DynamicClass::startupRun());
    VERIFY(LibStatic::libStartupRun());
    VERIFY(LibDynamic::libStartupRun());
    VERIFY(startuped);

    LibStatic stat;
    COMPARE(stat.magicNumber(), 422);
    COMPARE(stat.magicFraction(), 0.42);

    LibDynamic dyna;
    COMPARE(dyna.magicNumber(), 425);
    COMPARE(dyna.magicFraction(), 0.24);

    COMPARE(dummy_sta<int>(42), 42);
    COMPARE(dummy_dyn<int>(42), 42);

    VERIFY(QFile::exists(":/package2.txt"));
    VERIFY(QFile::exists(":/static.txt"));

    return 0;
}
