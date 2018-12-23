#ifndef SIMPLE_H
#define SIMPLE_H

#include <QObject>
#include <QString>

class Simple
{
    Q_GADGET

    Q_PROPERTY(QString value MEMBER value)

public:
    QString value;

    QString transform() const;
};

#endif