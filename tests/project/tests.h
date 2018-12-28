#ifndef TESTS_H
#define TESTS_H

#include <QDebug>

#define COMPARE_IMPL(x, y, file, line) do { \
    if((x) != (y)) { \
        qCritical().nospace() << file << ":" << line << ": COMPARE ERROR: " \
                              << #x << "{" << (x) << "}" << " != " << #y << "{" << (y) << "}"; \
        return 1; \
    } \
} while(false)

#define COMPARE(x, y) COMPARE_IMPL(x, y, __FILE__, __LINE__)

#define VERIFY_IMPL(x, file, line) do { \
    if(!(x)) { \
        qCritical().nospace() << file << ":" << line << ": VERIFY ERROR: !" << #x; \
        return 1; \
    } \
} while(false);

#define VERIFY(x) VERIFY_IMPL(x, __FILE__, __LINE__)

#endif
