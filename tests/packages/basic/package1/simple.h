#ifndef SIMPLE_H
#define SIMPLE_H

#include <QObject>
#include <QString>

class Simple
{
    Q_GADGET
    Q_DECLARE_TR_FUNCTIONS(Simple)

    Q_PROPERTY(QString value MEMBER value)

public:
    QString value;

    QString transform() const;
    QString translate() const;
};

#endif