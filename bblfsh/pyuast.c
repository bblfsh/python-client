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

static const char *GetInternalType(const void *node)
{
  return ReadStr(node, "internal_type");
}

static const char *GetToken(const void *node)
{
  return ReadStr(node, "token");
}

static int GetChildrenSize(const void *node)
{
  return ReadLen(node, "children");
}

static void *GetChild(const void *data, int index)
{
  PyObject *node = (PyObject *)data;
  PyObject *children_obj = PyObject_GetAttrString(node, "children");
  if (!children_obj)
    return NULL;

  PyObject *seq = PySequence_Fast(children_obj, "expected a sequence");
  return PyList_GET_ITEM(seq, index);
}

static int GetRolesSize(const void *node)
{
  return ReadLen(node, "roles");
}

static uint16_t GetRoleAt(const void *data, int index)
{
  PyObject *node = (PyObject *)data;
  PyObject *roles_obj = PyObject_GetAttrString(node, "roles");
  if (!roles_obj)
    return 0;
  PyObject *seq = PySequence_Fast(roles_obj, "expected a sequence");
  return (uint16_t)PyLong_AsUnsignedLong(PyList_GET_ITEM(seq, index));
}

static int GetPropertiesSize(const void *data)
{
  PyObject *node = (PyObject *)data;
  PyObject *properties_obj = PyObject_GetAttrString(node, "properties");
  if (!properties_obj)
    return 0;

  return (int)PyLong_AsLong(properties_obj);
}

static const char *GetPropertyAt(const void *data, int index)
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

static PyObject *PyFind(PyObject *self, PyObject *args)
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
    {"find", PyFind, METH_VARARGS, "Find a node in the UAST"},
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
    .InternalType = GetInternalType,
    .Token = GetToken,
    .ChildrenSize = GetChildrenSize,
    .ChildAt = GetChild,
    .RolesSize = GetRolesSize,
    .RoleAt = GetRoleAt,
    .PropertiesSize = GetPropertiesSize,
    .PropertyAt = GetPropertyAt,
  };

  ctx = UastNew(iface);
  return PyModule_Create(&module_def);
}
