#include <cstdint>
#include <cstdlib>
#include <cstring>

#include <Python.h>

#include "uast.h"
#include "memtracker.h"



// Used to store references to the Pyobjects instanced in String() and
// ItemAt() methods. Those can't be DECREF'ed to 0 because libuast uses them
// so we pass ownership to these lists and free them at the end of filter()
MemTracker memTracker;

// WARNING: calls to Attribute MUST Py_DECREF the returned value once
// used (or add it to the memtracker)
static PyObject *Attribute(const void *node, const char *prop) {
  PyObject *n = (PyObject *)node;
  return PyObject_GetAttrString(n, prop);
}

// WARNING: calls to AttributeValue MUST Py_DECREF the returned value once
// used (or add it to the memtracker)
static PyObject *AttributeValue(const void *node, const char *prop) {
  PyObject *a = Attribute(node, prop);
  return a && a != Py_None ? a : NULL;
}

static bool HasAttribute(const void *node, const char *prop) {
  PyObject *o = AttributeValue(node, prop);
  if (o == NULL) {
    return false;
  }

  Py_DECREF(o);
  return true;
}

static const char *String(const void *node, const char *prop) {
  const char *retval = NULL;
  PyObject *o = Attribute(node, prop);
  if (o != NULL) {
    retval = PyUnicode_AsUTF8(o);
    memTracker.TrackItem(o);
  }
  return retval;
}

static size_t Size(const void *node, const char *prop) {
  size_t retval = 0;
  PyObject *o = Attribute(node, prop);
  if (o != NULL) {
    retval = PySequence_Size(o);
    Py_DECREF(o);
  }

  return retval;
}

static PyObject *ItemAt(PyObject *object, int index) {
  PyObject *retval = NULL;
  PyObject *seq = PySequence_Fast(object, "expected a sequence");
  if (seq != NULL) {
    retval = PyList_GET_ITEM(seq, index);
    memTracker.TrackItem(seq);
  }

  return retval;
}

static const char *InternalType(const void *node) {
  return String(node, "internal_type");
}

static const char *Token(const void *node) {
  return String(node, "token");
}

static size_t ChildrenSize(const void *node) {
  return Size(node, "children");
}

static void *ChildAt(const void *node, int index) {
  PyObject *children = AttributeValue(node, "children");
  void *retval = nullptr;
  if (children) {
    retval = ItemAt(children, index);
    Py_DECREF(children);
  }

  return retval;
}

static size_t RolesSize(const void *node) {
  return Size(node, "roles");
}

static uint16_t RoleAt(const void *node, int index) {
  uint16_t retval = 0;
  PyObject *roles = AttributeValue(node, "roles");
  if (roles) {
    retval = (uint16_t)PyLong_AsUnsignedLong(ItemAt(roles, index));
    Py_DECREF(roles);
  }
  return retval;
}

static size_t PropertiesSize(const void *node) {
  size_t retval = 0;
  PyObject *properties = AttributeValue(node, "properties");
  if (properties) {
    retval = PyMapping_Size(properties);
    Py_DECREF(properties);
  }
  return retval;
}

static const char *PropertyKeyAt(const void *node, int index) {
  PyObject *properties = AttributeValue(node, "properties");
  if (!properties || !PyMapping_Check(properties)) {
    return NULL;
  }

  const char *retval = NULL;
  PyObject *keys = PyMapping_Keys(properties);
  Py_DECREF(properties);
  if (keys != NULL) {
    retval = PyUnicode_AsUTF8(ItemAt(keys, index));
    Py_DECREF(keys);
  }
  return retval;
}

static const char *PropertyValueAt(const void *node, int index) {
  PyObject *properties = AttributeValue(node, "properties");
  if (!properties)
    return NULL;

  if (!PyMapping_Check(properties)) {
    Py_DECREF(properties);
    return NULL;
  }

  const char *retval = NULL;
  PyObject *values = PyMapping_Values(properties);
  if (values != NULL) {
    retval = PyUnicode_AsUTF8(ItemAt(values, index));
    Py_DECREF(values);
  }
  Py_DECREF(properties);
  return retval;
}

static uint32_t PositionValue(const void* node, const char *prop, const char *field) {
  PyObject *position = AttributeValue(node, prop);
  if (!position) {
    return 0;
  }

  PyObject *offset = AttributeValue(position, field);
  Py_DECREF(position);
  uint32_t retval = 0;

  if (offset) {
    retval = (uint32_t)PyLong_AsUnsignedLong(offset);
    Py_DECREF(offset);
  }
  return retval;
}

/////////////////////////////////////
/////////// Node Interface //////////
/////////////////////////////////////

extern "C"
{
  static bool HasStartOffset(const void *node) {
    return HasAttribute(node, "start_position");
  }

  static uint32_t StartOffset(const void *node) {
    return PositionValue(node, "start_position", "offset");
  }

  static bool HasStartLine(const void *node) {
    return HasAttribute(node, "start_position");
  }

  static uint32_t StartLine(const void *node) {
    return PositionValue(node, "start_position", "line");
  }

  static bool HasStartCol(const void *node) {
    return HasAttribute(node, "start_position");
  }

  static uint32_t StartCol(const void *node) {
    return PositionValue(node, "start_position", "col");
  }

  static bool HasEndOffset(const void *node) {
    return HasAttribute(node, "end_position");
  }

  static uint32_t EndOffset(const void *node) {
    return PositionValue(node, "end_position", "offset");
  }

  static bool HasEndLine(const void *node) {
    return HasAttribute(node, "end_position");
  }

  static uint32_t EndLine(const void *node) {
    return PositionValue(node, "end_position", "line");
  }

  static bool HasEndCol(const void *node) {
    return HasAttribute(node, "end_position");
  }

  static uint32_t EndCol(const void *node) {
    return PositionValue(node, "end_position", "col");
  }
}
static Uast *ctx;

/////////////////////////////////////
/////////// PYTHON API //////////////
/////////////////////////////////////
typedef struct {
  PyObject_HEAD
  UastIterator *iter;
} PyUastIter;

// iterator.__iter__()
static PyObject *PyUastIter_iter(PyObject *self)
{
  Py_INCREF(self);
  return self;
}

// iterator.__next__()
static PyObject *PyUastIter_next(PyObject *self)
{

  PyUastIter *it = (PyUastIter *)self;

  void *node = UastIteratorNext(it->iter);
  if (!node) {
    PyErr_SetNone(PyExc_StopIteration);
    return NULL;
  }

  Py_INCREF(node);
  memTracker.SetCurrentIterator(it->iter);
  return (PyObject *)node;
}

// Forward declaration for the Type ref
static PyObject *PyUastIter_new(PyObject *self, PyObject *args);
static void PyUastIter_dealloc(PyObject *self);

extern "C"
{
  static PyTypeObject PyUastIterType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "pyuast.UastIterator",          // tp_name
    sizeof(PyUastIter),             // tp_basicsize
    0,                              // tp_itemsize
    PyUastIter_dealloc,             // tp_dealloc
    0,                              // tp_print
    0,                              // tp_getattr
    0,                              // tp_setattr
    0,                              // tp_reserved
    0,                              // tp_repr
    0,                              // tp_as_number
    0,                              // tp_as_sequence
    0,                              // tp_as_mapping
    0,                              // tp_hash
    0,                              // tp_call
    0,                              // tp_str
    0,                              // tp_getattro
    0,                              // tp_setattro
    0,                              // tp_as_buffer
    Py_TPFLAGS_DEFAULT,             // tp_flags
    "Internal UastIterator object", // tp_doc
    0,                              // tp_traverse
    0,                              // tp_clear
    0,                              // tp_richcompare
    0,                              // tp_weaklistoffset
    PyUastIter_iter,                // tp_iter: __iter()__ method
    (iternextfunc)PyUastIter_next,  // tp_iternext: next() method
    0,                              // tp_methods
    0,                              // tp_members
    0,                              // tp_getset
    0,                              // tp_base
    0,                              // tp_dict
    0,                              // tp_descr_get
    0,                              // tp_descr_set
    0,                              // tp_dictoffset
    0,                              // tp_init
    PyType_GenericAlloc,            // tp_alloc
    0,                              // tp_new
  };
}

static PyObject *PyUastIter_new(PyObject *self, PyObject *args)
{
  void *node = NULL;
  uint8_t order;

  if (!PyArg_ParseTuple(args, "OB", &node, &order))
    return NULL;

  PyUastIter *pyIt = PyObject_New(PyUastIter, &PyUastIterType);
  if (!pyIt)
    return NULL;

  if (!PyObject_Init((PyObject *)pyIt, &PyUastIterType)) {
    Py_DECREF(pyIt);
    return NULL;
  }

  pyIt->iter = UastIteratorNew(ctx, node, (TreeOrder)order);
  if (!pyIt->iter) {
    Py_DECREF(pyIt);
    return NULL;
  }

  memTracker.ClearCurrentIterator();
  memTracker.SetCurrentIterator(pyIt->iter);
  return (PyObject*)pyIt;
}


static void PyUastIter_dealloc(PyObject *self)
{
  memTracker.DisposeMem();
  UastIteratorFree(((PyUastIter *)self)->iter);
}

static bool initFilter(PyObject *args, PyObject **obj, const char **query)
{
  if (!PyArg_ParseTuple(args, "Os", obj, query)) {
    return false;
  }

  memTracker.EnterFilter();
  return true;
}

static void cleanupFilter(void)
{

  memTracker.DisposeMem();
  memTracker.ExitFilter();
}

static void filterError(void)
{
  char *error = LastError();
  PyErr_SetString(PyExc_RuntimeError, error);
  free(error);
  cleanupFilter();
}

static PyObject *PyFilter(PyObject *self, PyObject *args)
{
  PyObject *obj = NULL;
  const char *query = NULL;

  if (!initFilter(args, &obj, &query)) {
    return NULL;
  }

  Nodes *nodes = UastFilter(ctx, obj, query);
  if (!nodes) {
    filterError();
    cleanupFilter();
    return NULL;
  }

  size_t len = NodesSize(nodes);
  PyObject *list = PyList_New(len);

  for (size_t i = 0; i < len; i++) {
    PyObject *node = (PyObject *)NodeAt(nodes, i);
    Py_INCREF(node);
    PyList_SET_ITEM(list, i, node);
  }
  NodesFree(nodes);
  PyObject *iter = PySeqIter_New(list);
  Py_DECREF(list);

  cleanupFilter();
  return iter;
}

static PyObject *PyFilterBool(PyObject *self, PyObject *args)
{
  PyObject *obj = NULL;
  const char *query = NULL;

  if (!initFilter(args, &obj, &query))
    return NULL;

  bool ok;
  bool res = UastFilterBool(ctx, obj, query, &ok);
  if (!ok) {
    filterError();
    return NULL;
  }

  cleanupFilter();
  return res ? Py_True : Py_False;
}

static PyObject *PyFilterNumber(PyObject *self, PyObject *args)
{
  PyObject *obj = NULL;
  const char *query = NULL;

  if (!initFilter(args, &obj, &query))
    return NULL;

  bool ok;
  double res = UastFilterNumber(ctx, obj, query, &ok);
  if (!ok) {
    filterError();
    return NULL;
  }

  cleanupFilter();
  return PyFloat_FromDouble(res);
}

static PyObject *PyFilterString(PyObject *self, PyObject *args)
{
  PyObject *obj = NULL;
  const char *query = NULL;

  if (!initFilter(args, &obj, &query))
    return NULL;

  const char *res = UastFilterString(ctx, obj, query);
  if (res == NULL) {
    filterError();
    return NULL;
  }

  cleanupFilter();
  return PyUnicode_FromString(res);
}
static PyMethodDef extension_methods[] = {
    {"filter", PyFilter, METH_VARARGS, "Filter nodes in the UAST using the given query"},
    {"iterator", PyUastIter_new, METH_VARARGS, "Get an iterator over a node"},
    {"filter_bool", PyFilterBool, METH_VARARGS, "For queries returning boolean values"},
    {"filter_number", PyFilterNumber, METH_VARARGS, "For queries returning boolean values"},
    {"filter_string", PyFilterString, METH_VARARGS, "For queries returning boolean values"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef module_def = {
    PyModuleDef_HEAD_INIT,
    "pyuast",
    NULL,
    -1,
    extension_methods,
    NULL,
    NULL,
    NULL,
    NULL
};

PyMODINIT_FUNC
PyInit_pyuast(void)
{
  NodeIface iface;
  iface.InternalType = InternalType;
  iface.Token = Token;
  iface.ChildrenSize = ChildrenSize;
  iface.ChildAt = ChildAt;
  iface.RolesSize = RolesSize;
  iface.RoleAt = RoleAt;
  iface.PropertiesSize = PropertiesSize;
  iface.PropertyKeyAt = PropertyKeyAt;
  iface.PropertyValueAt = PropertyValueAt;
  iface.HasStartOffset = HasStartOffset;
  iface.StartOffset = StartOffset;
  iface.HasStartLine = HasStartLine;
  iface.StartLine = StartLine;
  iface.HasStartCol = HasStartCol;
  iface.StartCol = StartCol;
  iface.HasEndOffset = HasEndOffset;
  iface.EndOffset = EndOffset;
  iface.HasEndLine = HasEndLine;
  iface.EndLine = EndLine;
  iface.HasEndCol = HasEndCol;
  iface.EndCol = EndCol;

  ctx = UastNew(iface);
  return PyModule_Create(&module_def);
}
