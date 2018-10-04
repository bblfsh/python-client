#include <unordered_map>
#include <vector>

#include <Python.h>

class MemTracker {
private:
  std::vector<PyObject*> filterItemAllocs_;

public:
  void TrackItem(PyObject *ref);
  void DisposeMem();
};
