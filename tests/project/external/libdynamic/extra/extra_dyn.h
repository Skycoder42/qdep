#ifndef EXTRA_DYN_H
#define EXTRA_DYN_H

#include <utility>

template <typename T>
T dummy_dyn(T &&data) { return std::move(data); }

#endif
