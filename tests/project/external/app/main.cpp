#include <QCoreApplication>
#include <tests.h>

#include <libstatic.h>
#include <libdynamic.h>

#include <extra_sta.h>
#include <extra_dyn.h>

int main(int argc, char **argv)
{
    QCoreApplication app{argc, argv};

    LibStatic stat;
    COMPARE(stat.magicNumber(), 422)
    COMPARE(stat.magicFraction(), 0.42)

    LibDynamic dyna;
    COMPARE(dyna.magicNumber(), 425)
    COMPARE(dyna.magicFraction(), 0.24)

    dummy_sta<int>(42);
    dummy_dyn<int>(42);

    return 0;
}
