#include "uast.h"

#include <stdint.h>

#include <Python.h>

static const char *ReadStr(const void *data, const char *prop)
{
  PyObject *node = (PyObject *)data;
  PyObject *attribute = PyObject_GetAttrString(node, prop);
  if (!attribute) {
    return NULL;
  }
  return PyUnicode_AsUTF8(attribute);
}

static int ReadLen(const void *data, const char *prop)
{
  PyObject *node = (PyObject *)data;
  PyObject *children_obj = PyObject_GetAttrString(node, prop);
  if (!children_obj)
    return 0;
  return PySequence_Size(children_obj);
}

static const char *InternalType(const void *node)
{
  return ReadStr(node, "internal_type");
}

static const char *Token(const void *node)
{
  return ReadStr(node, "token");
}

static int ChildrenSize(const void *node)
{
  return ReadLen(node, "children");
}

static void *ChildAt(const void *data, int index)
{
  PyObject *node = (PyObject *)data;
  PyObject *children_obj = PyObject_GetAttrString(node, "children");
  if (!children_obj)
    return NULL;

  PyObject *seq = PySequence_Fast(children_obj, "expected a sequence");
  return PyList_GET_ITEM(seq, index);
}

static int RolesSize(const void *node)
{
  return ReadLen(node, "roles");
}

static uint16_t RoleAt(const void *data, int index)
{
  PyObject *node = (PyObject *)data;
  PyObject *roles_obj = PyObject_GetAttrString(node, "roles");
  if (!roles_obj)
    return 0;
  PyObject *seq = PySequence_Fast(roles_obj, "expected a sequence");
  return (uint16_t)PyLong_AsUnsignedLong(PyList_GET_ITEM(seq, index));
}

static int PropertiesSize(const void *data)
{
  PyObject *node = (PyObject *)data;
  PyObject *properties_obj = PyObject_GetAttrString(node, "properties");
  if (!properties_obj)
    return 0;

  return (int)PyLong_AsLong(properties_obj);
}

static const char *PropertyAT(const void *data, int index)
{
  PyObject *node = (PyObject *)data;
  PyObject *properties_obj = PyObject_GetAttrString(node, "properties");
  if (!properties_obj)
    return NULL;

  PyObject *seq = PySequence_Fast(properties_obj, "expected a sequence");
  return PyUnicode_AsUTF8(PyList_GET_ITEM(seq, index));
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
  if (nodes) {
    int len = NodesSize(nodes);
    PyObject *list = PyList_New(len);

    for (int i = 0; i < len; i++) {
      PyList_SET_ITEM(list, i, (PyObject *) NodeAt(nodes, i));
    }

    NodesFree(nodes);
    return list;
  }

  NodesFree(nodes);
  Py_RETURN_NONE;
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
    .PropertyAt = PropertyAT,
  };

  ctx = UastNew(iface);
  return PyModule_Create(&module_def);
}
