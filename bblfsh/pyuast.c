#include "uast.h"

#include <stdbool.h>
#include <stdint.h>

#include <Python.h>

static const char *ReadStr(const void *data, const char *prop) {
  PyObject *node = (PyObject *)data;
  PyObject *attribute = PyObject_GetAttrString(node, prop);
  if (!attribute) {
    return NULL;
  }
  return PyUnicode_AsUTF8(attribute);
}

static int ReadLen(const void *data, const char *prop) {
  PyObject *node = (PyObject *)data;
  PyObject *children_obj = PyObject_GetAttrString(node, prop);
  if (!children_obj) {
    return 0;
  }
  return PySequence_Size(children_obj);
}

static const char *InternalType(const void *node) {
  return ReadStr(node, "internal_type");
}

static const char *Token(const void *node) {
  return ReadStr(node, "token");
}

static int ChildrenSize(const void *node) {
  return ReadLen(node, "children");
}

static void *ChildAt(const void *data, int index) {
  PyObject *node = (PyObject *)data;
  PyObject *children_obj = PyObject_GetAttrString(node, "children");
  if (!children_obj) {
    return NULL;
  }

  PyObject *seq = PySequence_Fast(children_obj, "expected a sequence");
  return PyList_GET_ITEM(seq, index);
}

static int RolesSize(const void *node) {
  return ReadLen(node, "roles");
}

static uint16_t RoleAt(const void *data, int index) {
  PyObject *node = (PyObject *)data;
  PyObject *roles_obj = PyObject_GetAttrString(node, "roles");
  if (!roles_obj) {
    return 0;
  }

  PyObject *seq = PySequence_Fast(roles_obj, "expected a sequence");
  return (uint16_t)PyLong_AsUnsignedLong(PyList_GET_ITEM(seq, index));
}

static int PropertiesSize(const void *data) {
  PyObject *node = (PyObject *)data;
  PyObject *properties_obj = PyObject_GetAttrString(node, "properties");
  if (!properties_obj) {
    return 0;
  }

  return (int)PyLong_AsLong(properties_obj);
}

static const char *PropertyKeyAt(const void *data, int index) {
  PyObject *node = (PyObject *)data;
  PyObject *properties = PyObject_GetAttrString(node, "properties");
  if (!properties) {
    return NULL;
  }
  if (!PyMapping_Check(properties)) {
    return NULL;
  }
  PyObject *keys = PyMapping_Keys(properties);
  if (!keys) {
    return NULL;
  }

  PyObject *seq = PySequence_Fast(keys, "expected a sequence");
  return PyUnicode_AsUTF8(PyList_GET_ITEM(seq, index));
}

static const char *PropertyValueAt(const void *data, int index) {
  PyObject *node = (PyObject *)data;
  PyObject *properties = PyObject_GetAttrString(node, "properties");
  if (!properties) {
    return NULL;
  }
  if (!PyMapping_Check(properties)) {
    return NULL;
  }
  PyObject *values = PyMapping_Values(properties);
  if (!values) {
    return NULL;
  }

  PyObject *seq = PySequence_Fast(values, "expected a sequence");
  return PyUnicode_AsUTF8(PyList_GET_ITEM(seq, index));
}

static bool HasStartOffset(const void *data) {
  PyObject *node = (PyObject *)data;
  if (!node) {
    return false;
  }
  return PyObject_GetAttrString(node, "start_position") != Py_None;
}

static uint32_t StartOffset(const void *data) {
  PyObject *node = (PyObject *)data;
  PyObject *position = PyObject_GetAttrString(node, "start_position");
  if (!position || position == Py_None) {
    return 0;
  }

  PyObject *offset = PyObject_GetAttrString(position, "offset");
  if (!offset) {
    return 0;
  }
  return PyLong_AsUnsignedLong(offset);
}

static bool HasStartLine(const void *data) {
  PyObject *node = (PyObject *)data;
  if (!node) {
    return false;
  }
  return PyObject_GetAttrString(node, "start_position") != Py_None;
}

static uint32_t StartLine(const void *data) {
  PyObject *node = (PyObject *)data;
  PyObject *position = PyObject_GetAttrString(node, "start_position");
  if (!position || position == Py_None) {
    return 0;
  }

  PyObject *line = PyObject_GetAttrString(position, "line");
  if (!line) {
    return 0;
  }
  return PyLong_AsUnsignedLong(line);
}

static bool HasStartCol(const void *data) {
  PyObject *node = (PyObject *)data;
  if (!node) {
    return false;
  }
  return PyObject_GetAttrString(node, "start_position") != Py_None;
}

static uint32_t StartCol(const void *data) {
  PyObject *node = (PyObject *)data;
  PyObject *position = PyObject_GetAttrString(node, "start_position");
  if (!position || position == Py_None) {
    return 0;
  }

  PyObject *col = PyObject_GetAttrString(position, "col");
  if (!col) {
    return 0;
  }
  return PyLong_AsUnsignedLong(col);
}

static bool HasEndOffset(const void *data) {
  PyObject *node = (PyObject *)data;
  if (!node) {
    return false;
  }
  return PyObject_GetAttrString(node, "end_position") != Py_None;
}

static uint32_t EndOffset(const void *data) {
  PyObject *node = (PyObject *)data;
  PyObject *position = PyObject_GetAttrString(node, "end_position");
  if (!position || position == Py_None) {
    return 0;
  }

  PyObject *offset = PyObject_GetAttrString(position, "offset");
  if (!offset) {
    return 0;
  }
  return PyLong_AsUnsignedLong(offset);
}

static bool HasEndLine(const void *data) {
  PyObject *node = (PyObject *)data;
  if (!node) {
    return false;
  }
  return PyObject_GetAttrString(node, "end_position") != Py_None;
}

static uint32_t EndLine(const void *data) {
  PyObject *node = (PyObject *)data;
  PyObject *position = PyObject_GetAttrString(node, "end_position");
  if (!position || position == Py_None) {
    return 0;
  }

  PyObject *line = PyObject_GetAttrString(position, "line");
  if (!line) {
    return 0;
  }
  return PyLong_AsUnsignedLong(line);
}

static bool HasEndCol(const void *data) {
  PyObject *node = (PyObject *)data;
  if (!node) {
    return false;
  }
  return PyObject_GetAttrString(node, "end_position") != Py_None;
}

static uint32_t EndCol(const void *data) {
  PyObject *node = (PyObject *)data;
  PyObject *position = PyObject_GetAttrString(node, "end_position");
  if (!position || position == Py_None) {
    return 0;
  }

  PyObject *col = PyObject_GetAttrString(position, "col");
  if (!col) {
    return 0;
  }
  return PyLong_AsUnsignedLong(col);
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
