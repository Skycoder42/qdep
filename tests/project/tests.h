#ifndef TESTS_H
#define TESTS_H

#include <QDebug>

#define COMPARE_IMPL(x, y, file, line) do { \
    if((x) != (y)) { \
        qCritical().nospace() << file << ":" << line << ": COMPARE ERROR: " \
                              << (x) << " != " << (y); \
        return 1; \
    } \
} while(false)

#define COMPARE(x, y) COMPARE_IMPL(x, y, __FILE__, __LINE__)

#endif
