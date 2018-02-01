#include <Python.h>

#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include "uast.h"

// Used to store references to the Pyobjects instanced in String() and
// ItemAt() methods. Those can't be DECREF'ed to 0 because libuast uses the
// so we pass ownership to these lists and free them at the end of filter()
static PyObject *stringAllocsList;
static PyObject *itemAtAllocsList;

static PyObject *Attribute(const void *node, const char *prop) {
  PyObject *n = (PyObject *)node;
  return PyObject_GetAttrString(n, prop);
}

static PyObject *AttributeValue(const void *node, const char *prop) {
  PyObject *a = Attribute(node, prop);
  return a && a != Py_None ? a : NULL;
}

static const char *String(const void *node, const char *prop) {
  const char *retval = NULL;
  PyObject *o = Attribute(node, prop);
  if (o != NULL) {
    retval = PyUnicode_AsUTF8(o);
    PyList_Append(stringAllocsList, o);
    Py_DECREF(o);
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
    PyList_Append(itemAtAllocsList, seq);
    Py_DECREF(seq);
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
  return children ? ItemAt(children, index) : NULL;
}

static size_t RolesSize(const void *node) {
  return Size(node, "roles");
}

static uint16_t RoleAt(const void *node, int index) {
  PyObject *roles = AttributeValue(node, "roles");
  return roles ? (uint16_t)PyLong_AsUnsignedLong(ItemAt(roles, index)) : 0;
}

static size_t PropertiesSize(const void *node) {
  PyObject *properties = AttributeValue(node, "properties");
  return properties ? PyMapping_Size(properties) : 0;
}

static const char *PropertyKeyAt(const void *node, int index) {
  PyObject *properties = AttributeValue(node, "properties");
  if (!properties || !PyMapping_Check(properties)) {
    return NULL;
  }

  const char *retval = NULL;
  PyObject *keys = PyMapping_Keys(properties);
  if (keys != NULL) {
    retval = PyUnicode_AsUTF8(ItemAt(keys, index));
    Py_DECREF(keys);
  }
  return retval;
}

static const char *PropertyValueAt(const void *node, int index) {
  PyObject *properties = AttributeValue(node, "properties");
  if (!properties || !PyMapping_Check(properties)) {
    return NULL;
  }

  const char *retval = NULL;
  PyObject *values = PyMapping_Values(properties);
  if (values != NULL) {
    retval = PyUnicode_AsUTF8(ItemAt(values, index));
    Py_DECREF(values);
  }
  return retval;
}

static uint32_t PositionValue(const void* node, const char *prop, const char *field) {
  PyObject *position = AttributeValue(node, prop);
  if (!position) {
    return 0;
  }

  PyObject *offset = AttributeValue(position, field);
  return offset ? (uint32_t)PyLong_AsUnsignedLong(offset) : 0;
}

static bool HasStartOffset(const void *node) {
  return AttributeValue(node, "start_position");
}

static uint32_t StartOffset(const void *node) {
  return PositionValue(node, "start_position", "offset");
}

static bool HasStartLine(const void *node) {
  return AttributeValue(node, "start_position");
}

static uint32_t StartLine(const void *node) {
  return PositionValue(node, "start_position", "line");
}

static bool HasStartCol(const void *node) {
  return AttributeValue(node, "start_position");
}

static uint32_t StartCol(const void *node) {
  return PositionValue(node, "start_position", "col");
}

static bool HasEndOffset(const void *node) {
  return AttributeValue(node, "end_position");
}

static uint32_t EndOffset(const void *node) {
  return PositionValue(node, "end_position", "offset");
}

static bool HasEndLine(const void *node) {
  return AttributeValue(node, "end_position");
}

static uint32_t EndLine(const void *node) {
  return PositionValue(node, "end_position", "line");
}

static bool HasEndCol(const void *node) {
  return AttributeValue(node, "end_position");
}

static uint32_t EndCol(const void *node) {
  return PositionValue(node, "end_position", "col");
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
  return (PyObject *)node;
}

// Forward declaration for the Type ref
static PyObject *PyUastIter_new(PyObject *self, PyObject *args);
static void PyUastIter_dealloc(PyObject *self);

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

  return (PyObject*)pyIt;
}


static void PyUastIter_dealloc(PyObject *self)
{
  UastIteratorFree(((PyUastIter *)self)->iter);
}

static PyObject *PyFilter(PyObject *self, PyObject *args)
{
  PyObject *obj = NULL;
  const char *query = NULL;

  if (!PyArg_ParseTuple(args, "Os", &obj, &query)) {
    return NULL;
  }

  itemAtAllocsList = PyList_New(0);
  stringAllocsList = PyList_New(0);

  Nodes *nodes = UastFilter(ctx, obj, query);
  if (!nodes) {
    char *error = LastError();
    PyErr_SetString(PyExc_RuntimeError, error);
    free(error);
    Py_DECREF(stringAllocsList);
    Py_DECREF(itemAtAllocsList);
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

  Py_DECREF(itemAtAllocsList);
  Py_DECREF(stringAllocsList);
  return iter;
}

static PyMethodDef extension_methods[] = {
    {"filter", PyFilter, METH_VARARGS, "Filter nodes in the UAST using the given query"},
    {"iterator", PyUastIter_new, METH_VARARGS, "Get an iterator over a node"},
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
  NodeIface iface = {
    .InternalType = InternalType,
    .Token = Token,
    .ChildrenSize = ChildrenSize,
    .ChildAt = ChildAt,
    .RolesSize = RolesSize,
    .RoleAt = RoleAt,
    .PropertiesSize = PropertiesSize,
    .PropertyKeyAt = PropertyKeyAt,
    .PropertyValueAt = PropertyValueAt,
    .HasStartOffset = HasStartOffset,
    .StartOffset = StartOffset,
    .HasStartLine = HasStartLine,
    .StartLine = StartLine,
    .HasStartCol = HasStartCol,
    .StartCol = StartCol,
    .HasEndOffset = HasEndOffset,
    .EndOffset = EndOffset,
    .HasEndLine = HasEndLine,
    .EndLine = EndLine,
    .HasEndCol = HasEndCol,
    .EndCol = EndCol,
  };

  ctx = UastNew(iface);
  return PyModule_Create(&module_def);
}
