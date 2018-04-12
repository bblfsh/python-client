#include <unordered_map>
#include <vector>

#include "uast.h"

#include <Python.h>

class MemTracker {
private:
  UastIterator *currentIter_ = nullptr;
  bool inFilter_ = false;

  std::unordered_map<UastIterator*, std::vector<PyObject*>> iterItemAllocs_;
  std::vector<PyObject*> filterItemAllocs_;

public:
  UastIterator *CurrentIterator();
  void SetCurrentIterator(UastIterator *iter);
  bool CurrentIteratorSet();
  void ClearCurrentIterator();
  void EnterFilter();
  void ExitFilter();
  void TrackItem(PyObject *ref);
  void DisposeMem();
};
