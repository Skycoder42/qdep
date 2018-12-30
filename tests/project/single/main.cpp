#include <QCoreApplication>
#include <QTranslator>
#include <QLocale>
#include <tests.h>

#include <simple.h>

int main(int argc, char **argv)
{
    QCoreApplication app{argc, argv};
    auto translator = new QTranslator{&app};
    auto ts_ok = translator->load(QLocale{QLocale::German, QLocale::Germany},
                                  QStringLiteral("single"),
                                  QStringLiteral("_"),
                                  QStringLiteral(TS_DIR));
    VERIFY(ts_ok);
    VERIFY(QCoreApplication::installTranslator(translator));

    Simple simple;
    simple.value = QCoreApplication::translate("GLOBAL", "Hello Tree");
    COMPARE(simple.transform(), QLatin1String("hallo baum"));
    COMPARE(simple.translate(), QLatin1String("Hallo Welt"));
    return 0;
}
