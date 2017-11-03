#include <Python.h>

#include <stdbool.h>
#include <stdint.h>

#include "uast.h"

static PyObject *Attribute(const void *node, const char *prop) {
  PyObject *n = (PyObject *)node;
  return PyObject_GetAttrString(n, prop);
}

static PyObject *AttributeValue(const void *node, const char *prop) {
  PyObject *a = Attribute(node, prop);
  return a && a != Py_None ? a : NULL;
}

static const char *String(const void *node, const char *prop) {
  PyObject *o = Attribute(node, prop);
  return o ? PyUnicode_AsUTF8(o) : NULL;
}

static int Size(const void *node, const char *prop) {
  PyObject *o = Attribute(node, prop);
  return o ? PySequence_Size(o) : 0;
}

static PyObject *ItemAt(PyObject *object, int index) {
  PyObject *seq = PySequence_Fast(object, "expected a sequence");
  return PyList_GET_ITEM(seq, index);
}


static const char *InternalType(const void *node) {
  return String(node, "internal_type");
}

static const char *Token(const void *node) {
  return String(node, "token");
}

static int ChildrenSize(const void *node) {
  return Size(node, "children");
}

static void *ChildAt(const void *node, int index) {
  PyObject *children = AttributeValue(node, "children");
  return children ? ItemAt(children, index) : NULL;
}

static int RolesSize(const void *node) {
  return Size(node, "roles");
}

static uint16_t RoleAt(const void *node, int index) {
  PyObject *roles = AttributeValue(node, "roles");
  return roles ? (uint16_t)PyLong_AsUnsignedLong(ItemAt(roles, index)) : 0;
}

static int PropertiesSize(const void *node) {
  PyObject *properties = AttributeValue(node, "properties");
  return properties ? PyMapping_Size(properties) : 0;
}

static const char *PropertyKeyAt(const void *node, int index) {
  PyObject *properties = AttributeValue(node, "properties");
  if (!properties || !PyMapping_Check(properties)) {
    return NULL;
  }

  PyObject *keys = PyMapping_Keys(properties);
  return keys ? PyUnicode_AsUTF8(ItemAt(keys, index)) : NULL;
}

static const char *PropertyValueAt(const void *node, int index) {
  PyObject *properties = AttributeValue(node, "properties");
  if (!properties || !PyMapping_Check(properties)) {
    return NULL;
  }

  PyObject *values = PyMapping_Values(properties);
  return values ? PyUnicode_AsUTF8(ItemAt(values, index)) : NULL;
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

static PyObject *PyFilter(PyObject *self, PyObject *args)
{
  PyObject *obj = NULL;
  const char *query = NULL;
  if (!PyArg_ParseTuple(args, "Os", &obj, &query))
    return NULL;

  Nodes *nodes = UastFilter(ctx, obj, query);
  if (!nodes) {
    char *error = LastError();
    PyErr_SetString(PyExc_RuntimeError, error);
    free(error);
    return NULL;
  }
  int len = NodesSize(nodes);
  PyObject *list = PyList_New(len);

  for (int i = 0; i < len; i++) {
    PyObject *node = (PyObject *)NodeAt(nodes, i);
    Py_INCREF(node);
    PyList_SET_ITEM(list, i, node);
  }
  NodesFree(nodes);
  return PySeqIter_New(list);
}

static PyMethodDef extension_methods[] = {
    {"filter", PyFilter, METH_VARARGS, "Filter nodes in the UAST using the given query"},
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

PyMODINIT_FUNC PyInit_pyuast(void)
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
