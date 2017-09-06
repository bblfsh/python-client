#include <stdint.h>

#include <Python.h>

#include "uast.h"

static const char *read_str(const void *data, const char *prop)
{
  PyObject *node = (PyObject *)data;
  PyObject *attribute = PyObject_GetAttrString(node, prop);
  return PyUnicode_AsUTF8(attribute);
}

static int read_len(const void *data, const char *prop)
{
  PyObject *node = (PyObject *)data;
  PyObject *children_obj = PyObject_GetAttrString(node, prop);
  PyObject *seq = PySequence_Fast(children_obj, "expected a sequence");
  return PySequence_Size(children_obj);
}

static const char *get_internal_type(const void *node)
{
  return read_str(node, "internal_type");
}

static const char *get_token(const void *node)
{
  return read_str(node, "token");
}

static int get_children_size(const void *node)
{
  return read_len(node, "children");
}

static void *get_child(const void *data, int index)
{
  PyObject *node = (PyObject *)data;
  PyObject *children_obj = PyObject_GetAttrString(node, "children");
  PyObject *seq = PySequence_Fast(children_obj, "expected a sequence");
  return PyList_GET_ITEM(seq, index);
}

static int get_roles_size(const void *node)
{
  return read_len(node, "roles");
}

static uint16_t get_role(const void *data, int index)
{
  PyObject *node = (PyObject *)data;
  PyObject *roles_obj = PyObject_GetAttrString(node, "roles");
  PyObject *seq = PySequence_Fast(roles_obj, "expected a sequence");
  return (uint16_t)PyLong_AsUnsignedLong(PyList_GET_ITEM(seq, index));
}

static node_api *api;

/////////////////////////////////////
/////////// PYTHON API //////////////
/////////////////////////////////////

static PyObject *py_find(PyObject *self, PyObject *args)
{
  PyObject *obj = NULL;
  const char *query = NULL;
  if (!PyArg_ParseTuple(args, "Os", &obj, &query))
  {
    return NULL;
  }

  find_ctx *ctx = new_find_ctx();
  if (node_api_find(api, ctx, obj, query) == 0)
  {
    int len = find_ctx_get_len(ctx);
    PyObject *list = PyList_New(len);
    for (int i = 0; i < len; i++)
    {
      PyList_SET_ITEM(list, i, (PyObject *)find_ctx_get(ctx, i));
    }
    free_find_ctx(ctx);
    return list;
  }
  free_find_ctx(ctx);
  Py_RETURN_NONE;
}

static PyMethodDef extension_methods[] = {
    {"find", py_find, METH_VARARGS, "Find a node in the UAST"},
    {NULL, NULL, 0, NULL}};

static struct PyModuleDef moduledef = {
    PyModuleDef_HEAD_INIT,
    "pyuast",
    NULL,
    -1,
    extension_methods,
    NULL,
    NULL,
    NULL,
    NULL};

PyMODINIT_FUNC PyInit_pyuast(void)
{
  api = new_node_api((node_iface){
      .internal_type = get_internal_type,
      .token = get_token,
      .children_size = get_children_size,
      .children = get_child,
      .roles_size = get_roles_size,
      .roles = get_role,
  });
  return PyModule_Create(&moduledef);
}
