#ifndef EXTRA_STA_H
#define EXTRA_STA_H

#include <utility>

template <typename T>
T dummy_sta(T &&data) { return std::move(data); }

#endif
