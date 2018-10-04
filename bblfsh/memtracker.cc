#include "memtracker.h"

void MemTracker::TrackItem(PyObject *o)
{
  filterItemAllocs_.push_back(o);
}

void MemTracker::DisposeMem()
{
    for (auto &i : filterItemAllocs_) {
      Py_CLEAR(i);
    }
    filterItemAllocs_.clear();
    filterItemAllocs_.shrink_to_fit();
}
