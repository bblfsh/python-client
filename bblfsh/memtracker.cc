#include "memtracker.h"

UastIterator* MemTracker::CurrentIterator() { return currentIter_; }
void MemTracker::ClearCurrentIterator() { currentIter_ = nullptr; }
void MemTracker::EnterFilter() { inFilter_ = true; }
void MemTracker::ExitFilter() { inFilter_ = false; }
bool MemTracker::CurrentIteratorSet() { return currentIter_ != nullptr; }
void MemTracker::SetCurrentIterator(UastIterator *iter) { currentIter_ = iter; }

void MemTracker::TrackItem(PyObject *o)
{
  if (inFilter_) {
    filterItemAllocs_.push_back(o);
  } else {
    iterItemAllocs_[currentIter_].push_back(o);
  }
}

void MemTracker::TrackStr(PyObject *o)
{
  if (inFilter_) {
    filterStrAllocs_.push_back(o);
  } else {
    iterStrAllocs_[currentIter_].push_back(o);
  }
}

void MemTracker::DisposeMem()
{
  if (inFilter_) {
    for (auto &i : filterStrAllocs_) {
      Py_XDECREF(i);
      i = nullptr;
    }
    for (auto &i : filterItemAllocs_) {
      Py_XDECREF(i);
      i = nullptr;
    }
  } else {
    for (auto &i : iterStrAllocs_[currentIter_]) {
      Py_XDECREF(i);
      i = nullptr;
    }
    for (auto &i : iterItemAllocs_[currentIter_]) {
      Py_XDECREF(i);
      i = nullptr;
    }
    ClearCurrentIterator();
  }
}
