#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <map>

#include <Python.h>
#include <structmember.h>

#include "libuast.hpp"

// Used to store references to the Pyobjects instanced in String() and
// ItemAt() methods. Those can't be DECREF'ed to 0 because libuast uses them
// so we pass ownership to these lists and free them at the end of filter()

PyObject* asPyBuffer(uast::Buffer buf) {
    return PyByteArray_FromStringAndSize((const char*)(buf.ptr), buf.size);
    //return PyMemoryView_FromMemory((char*)(buf.ptr), buf.size, PyBUF_READ);
}

/*
static bool checkError(const Uast* ctx) {
    char *error = LastError((Uast*)ctx);
    if (!error) {
        return true;
    }
    PyErr_SetString(PyExc_RuntimeError, error);
    free(error);
    return false;
}
*/

// ==========================================
//  External UAST Node (managed by libuast)
// ==========================================

class ContextExt;

typedef struct {
  PyObject_HEAD
  ContextExt    *ctx;
  NodeHandle handle;
} PyNodeExt;

static PyObject *PyNodeExt_load(PyNodeExt *self, PyObject *Py_UNUSED(ignored));

static PyMethodDef PyNodeExt_methods[] = {
    {"load", (PyCFunction) PyNodeExt_load, METH_NOARGS,
     "Load external node to Python"
    },
    {nullptr}  // Sentinel
};

extern "C"
{
    static PyTypeObject PyNodeExtType = {
      PyVarObject_HEAD_INIT(nullptr, 0)
      "pyuast.NodeExt",               // tp_name
      sizeof(PyNodeExt),                // tp_basicsize
      0,                              // tp_itemsize
      0,                              // tp_dealloc
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
      "External UAST node",           // tp_doc
      0,                              // tp_traverse
      0,                              // tp_clear
      0,                              // tp_richcompare
      0,                              // tp_weaklistoffset
      0,                              // tp_iter: __iter()__ method
      0,                              // tp_iternext: next() method
      PyNodeExt_methods,                // tp_methods
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

// ==========================================
//          External UAST iterator
// ==========================================

typedef struct {
  PyObject_HEAD
  ContextExt *ctx;
  uast::Iterator<NodeHandle> *iter;
  bool freeCtx;
} PyUastIterExt;

static void PyUastIterExt_dealloc(PyObject *self);

static PyObject *PyUastIterExt_iter(PyObject *self) {
  Py_INCREF(self);
  return self;
}

static PyObject *PyUastIterExt_toPy(ContextExt *ctx, NodeHandle node);

static PyObject *PyUastIterExt_next(PyObject *self) {
  auto it = (PyUastIterExt *)self;

  // TODO: check errors
  if (!it->iter->next()) {
    PyErr_SetNone(PyExc_StopIteration);
    return nullptr;
  }

  NodeHandle node = it->iter->node();
  if (node == 0) Py_RETURN_NONE;

  return PyUastIterExt_toPy(it->ctx, node);
}

extern "C"
{
  static PyTypeObject PyUastIterExtType = {
    PyVarObject_HEAD_INIT(nullptr, 0)
    "pyuast.IteratorExt",           // tp_name
    sizeof(PyUastIterExt),          // tp_basicsize
    0,                              // tp_itemsize
    PyUastIterExt_dealloc,          // tp_dealloc
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
    "External UastIterator object", // tp_doc
    0,                              // tp_traverse
    0,                              // tp_clear
    0,                              // tp_richcompare
    0,                              // tp_weaklistoffset
    PyUastIterExt_iter,                // tp_iter: __iter()__ method
    (iternextfunc)PyUastIterExt_next,  // tp_iternext: next() method
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

// ==========================================
// External UAST Context (managed by libuast)
// ==========================================

class ContextExt {
private:
    uast::Context<NodeHandle> *ctx;

    // toPy allocates a new NodeExt with a specified handle.
    // Returns a new reference.
    PyObject* toPy(NodeHandle node) {
        if (node == 0) Py_RETURN_NONE;

        PyNodeExt *pyObj = PyObject_New(PyNodeExt, &PyNodeExtType);
        if (!pyObj) return nullptr;

        pyObj->ctx = this;
        pyObj->handle = node;
        return (PyObject*)pyObj;
    }

    // toHandle casts an object to NodeExt and returns its handle.
    // Borrows the reference.
    NodeHandle toHandle(PyObject* obj) {
        if (!obj || obj == Py_None) return 0;

        if (!PyObject_TypeCheck(obj, &PyNodeExtType)) {
            const char* err = "unknown node type";
            PyErr_SetString(PyExc_NotImplementedError, err);
            ctx->SetError(err);
            return 0;
        }

        auto node = (PyNodeExt*)obj;
        return node->handle;
    }

    PyObject* newIter(uast::Iterator<NodeHandle> *it, bool freeCtx){
        PyUastIterExt *pyIt = PyObject_New(PyUastIterExt, &PyUastIterExtType);
        if (!pyIt)
          return nullptr;

        if (!PyObject_Init((PyObject *)pyIt, &PyUastIterExtType)) {
          Py_DECREF(pyIt);
          return nullptr;
        }
        pyIt->iter = it;
        pyIt->ctx = this;
        pyIt->freeCtx = freeCtx;
        return (PyObject*)pyIt;
    }
public:
    friend class Context;

    ContextExt(uast::Context<NodeHandle> *c) : ctx(c) {
    }
    ~ContextExt(){
        delete(ctx);
    }

    // lookup searches for a specific node handle.
    // Returns a new reference.
    PyObject* lookup(NodeHandle node) {
        return toPy(node);
    }

    // RootNode returns a root UAST node, if set.
    // Returns a new reference.
    PyObject* RootNode(){
        NodeHandle root = ctx->RootNode();
        return lookup(root);
    }

    // Iterate iterates over an external UAST tree.
    // Borrows the reference.
    PyObject* Iterate(PyObject* node, TreeOrder order){
        NodeHandle h = toHandle(node);
        auto iter = ctx->Iterate(h, order);
        return newIter(iter, false);
    }

    // Filter queries an external UAST.
    // Borrows the reference.
    PyObject* Filter(PyObject* node, char* query){
        NodeHandle unode = toHandle(node);
        if (unode == 0) {
          unode = ctx->RootNode();
        }

        uast::Iterator<NodeHandle> *it = ctx->Filter(unode, query);
        delete(query);
        return newIter(it, false);
    }

    // Encode serializes the external UAST.
    // Borrows the reference.
    PyObject* Encode(PyObject *node, UastFormat format) {
        uast::Buffer data = ctx->Encode(toHandle(node), format);
        return asPyBuffer(data);
    }
};

// PyUastIterExt_toPy is a function that looks up for nodes visited by iterator.
// Returns a new reference.
static PyObject *PyUastIterExt_toPy(ContextExt *ctx, NodeHandle node) {
  return ctx->lookup(node);
}

// PyUastIterExt_dealloc destroys an iterator.
static void PyUastIterExt_dealloc(PyObject *self) {
  auto it = (PyUastIterExt *)self;
  delete(it->iter);

  if (it->freeCtx && it->ctx) {
    delete(it->ctx);
  }
  it->freeCtx = false;
  it->ctx = nullptr;
}

typedef struct {
  PyObject_HEAD
  ContextExt *p;
} PyContextExt;

static void PyContextExt_dealloc(PyObject *self) {
  delete(((PyContextExt *)self)->p);
  // TODO: delete self?
}

// PyContextExt_root returns a root node associated with this context.
// Returns a new reference.
static PyObject *PyContextExt_root(PyContextExt *self, PyObject *Py_UNUSED(ignored)) {
    return self->p->RootNode();
}

// PyContextExt_filter filters UAST.
// Returns a new reference.
static PyObject *PyContextExt_filter(PyContextExt *self, PyObject *args) {
    PyObject *node = nullptr;
    char *query = nullptr;
    if (!PyArg_ParseTuple(args, "Os", &node, &query))
      return nullptr;
    return self->p->Filter(node, query);
}

// PyContextExt_filter serializes UAST.
// Returns a new reference.
static PyObject *PyContextExt_encode(PyContextExt *self, PyObject *args) {
    PyObject *node = nullptr;
    UastFormat format = UAST_BINARY; // TODO: make it a kwarg and enum
    if (!PyArg_ParseTuple(args, "Oi", &node, &format))
      return nullptr;
    return self->p->Encode(node, format);
}

static PyMethodDef PyContextExt_methods[] = {
    {"root", (PyCFunction) PyContextExt_root, METH_NOARGS,
     "Return the root node attached to this query context"
    },
    {"filter", (PyCFunction) PyContextExt_filter, METH_VARARGS,
     "Filter a provided UAST with XPath"
    },
    {"encode", (PyCFunction) PyContextExt_encode, METH_VARARGS,
     "Encodes a UAST into a buffer"
    },
    {nullptr}  // Sentinel
};

extern "C"
{
    static PyTypeObject PyContextExtType = {
      PyVarObject_HEAD_INIT(nullptr, 0)
      "pyuast.ContextExt",               // tp_name
      sizeof(PyContextExt),                 // tp_basicsize
      0,                              // tp_itemsize
      PyContextExt_dealloc,                 // tp_dealloc
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
      "Internal ContextExt object",      // tp_doc
      0,                              // tp_traverse
      0,                              // tp_clear
      0,                              // tp_richcompare
      0,                              // tp_weaklistoffset
      0,                              // tp_iter: __iter()__ method
      0,                              // tp_iternext: next() method
      PyContextExt_methods,                 // tp_methods
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

// ================================================
// Python UAST Node interface (called from libuast)
// ================================================

class Interface;

class Node : public uast::Node<Node*> {
private:
    Interface* ctx;
    PyObject* obj; // Node owns a reference
    NodeKind  kind;

    PyObject* keys;
    std::string* str;

    // checkPyException checks a Python error status, and if it's set, throws an error.
    static void checkPyException() {
        PyObject *type, *value, *traceback;
        PyErr_Fetch(&type, &value, &traceback);
        if (value == nullptr || value == Py_None) {
            return;
        }
        Py_DECREF(type);
        Py_DECREF(traceback);

        PyObject* str = PyObject_Str(value);
        Py_DECREF(value);

        auto err = PyUnicode_AsUTF8(str);
        Py_DECREF(str);

        throw std::runtime_error(err);
    }

    // kindOf returns a kind of a Python object.
    // Borrows the reference.
    static NodeKind kindOf(PyObject* obj) {
        if (!obj || obj == Py_None) {
          return NODE_nullptr;
        } else if (PyUnicode_Check(obj)) {
          return NODE_STRING;
        } else if (PyLong_Check(obj)) {
          return NODE_INT;
        } else if (PyFloat_Check(obj)) {
          return NODE_FLOAT;
        } else if (PyBool_Check(obj)) {
          return NODE_BOOL;
        } else if (PyList_Check(obj)) {
          return NODE_ARRAY;
        }
        return NODE_OBJECT;
    }
    Node* lookupOrCreate(PyObject* obj);
public:
    friend class Interface;
    friend class Context;

    // Node creates a new node associated with a given Python object and sets the kind.
    // Steals the reference.
    Node(Interface* c, NodeKind k, PyObject* v) : keys(nullptr), str(nullptr) {
        ctx = c;
        obj = v;
        kind = k;
    }
    // Node creates a new node associated with a given Python object and automatically determines the kind.
    // Creates a new reference.
    Node(Interface* c, PyObject* v) : keys(nullptr), str(nullptr) {
        ctx = c;
        obj = v; Py_INCREF(v);
        kind = kindOf(v);
    }
    ~Node(){
        if (keys) {
            Py_DECREF(keys);
            keys = nullptr;
        }
        if (obj) {
            Py_DECREF(obj);
        }
        if (str) {
            delete str;
        }
    }

    PyObject* toPy();

    NodeKind Kind() {
        return kind;
    }
    std::string* AsString() {
        if (!str) {
            const char* s = PyUnicode_AsUTF8(obj);
            str = new std::string(s);
        }

        std::string* s = new std::string(*str);
        return s;
    }
    int64_t AsInt() {
        long long v = PyLong_AsLongLong(obj);
        return (int64_t)(v);
    }
    uint64_t AsUint() {
        unsigned long long v = PyLong_AsUnsignedLongLong(obj);
        return (uint64_t)(v);
    }
    double AsFloat() {
        double v = PyFloat_AsDouble(obj);
        return (double)(v);
    }
    bool AsBool() {
        return obj == Py_True;
    }
    
    size_t Size() {
        size_t sz = 0;
        if (PyList_Check(obj)) {
            sz = (size_t)(PyList_Size(obj));
        } else {
            sz = (size_t)(PyObject_Size(obj));
            if (int64_t(sz) == -1) {
                checkPyException();
                return 0; // error
            }
        }
        assert(int64_t(sz) >= 0);
        return sz;
    }
    
    std::string* KeyAt(size_t i) {
        if (obj == Py_None) {
            return nullptr;
        }
        if (!keys) keys = PyDict_Keys(obj);
        PyObject* key = PyList_GetItem(keys, i); // borrows
        const char * k = PyUnicode_AsUTF8(key);

        std::string* s = new std::string(k);
        return s;
    }
    Node* ValueAt(size_t i) {
        if (obj == Py_None) {
            return nullptr;
        }
        if (PyList_Check(obj)) {
            PyObject* v = PyList_GetItem(obj, i); // borrows
            return lookupOrCreate(v); // new ref
        }
        if (!keys) keys = PyDict_Keys(obj);
        PyObject* key = PyList_GetItem(keys, i); // borrows
        PyObject* val = PyDict_GetItem(obj, key); // borrows

        return lookupOrCreate(val); // new ref
    }
    
    void SetValue(size_t i, Node* val) {
        PyObject* v = nullptr;
        if (val && val->obj) {
            v = val->obj;
        } else {
            v = Py_None;
        }
        Py_INCREF(v);
        PyList_SetItem(obj, i, v); // steals
    }
    void SetKeyValue(std::string k, Node* val) {
        PyObject* v = nullptr;
        if (val && val->obj) {
            v = val->obj;
        } else {
            v = Py_None;
        }
        PyDict_SetItemString(obj, k.data(), v); // new ref
    }
};

// ===========================================
// Python UAST interface (called from libuast)
// ===========================================

class Context;

class Interface : public uast::NodeCreator<Node*> {
private:
    std::map<PyObject*, Node*> obj2node;
    
    static PyObject* newBool(bool v) {
        if (v) {
            Py_RETURN_TRUE;
        }
        Py_RETURN_FALSE;
    }

    // lookupOrCreate either creates a new object or returns existing one.
    // In the second case it creates a new reference.
    Node* lookupOrCreate(PyObject* obj) {
        if (!obj || obj == Py_None) return nullptr;

        Node* node = obj2node[obj];
        if (node) return node;

        node = new Node(this, obj);
        obj2node[obj] = node;
        return node;
    }

    // create makes a new object with a specified kind.
    // Steals the reference.
    Node* create(NodeKind kind, PyObject* obj) {
        Node* node = new Node(this, kind, obj);
        obj2node[obj] = node;
        return node;
    }
public:
    friend class Node;
    friend class Context;

    Interface(){
    }
    ~Interface(){
        // Only needs to deallocate Nodes, since they own
        // the same object as used in the map key.
        for (auto it : obj2node) {
            delete(it.second);
        }
    }

    // toNode creates a new or returns an existing node associated with Python object.
    // Creates a new reference.
    Node* toNode(PyObject* obj){
        return lookupOrCreate(obj);
    }

    // toPy returns a Python object associated with a node.
    // Returns a new reference.
    PyObject* toPy(Node* node) {
        if (node == nullptr) Py_RETURN_NONE;
        Py_INCREF(node->obj);
        return node->obj;
    }

    Node* NewObject(size_t size) {
        PyObject* m = PyDict_New();
        return create(NODE_OBJECT, m);
    }
    Node* NewArray(size_t size) {
        PyObject* arr = PyList_New(size);
        return create(NODE_ARRAY, arr);
    }
    Node* NewString(std::string v) {
        PyObject* obj = PyUnicode_FromString(v.data());
        return create(NODE_STRING, obj);
    }
    Node* NewInt(int64_t v) {
        PyObject* obj = PyLong_FromLongLong(v);
        return create(NODE_INT, obj);
    }
    Node* NewUint(uint64_t v) {
        PyObject* obj = PyLong_FromUnsignedLongLong(v);
        return create(NODE_UINT, obj);
    }
    Node* NewFloat(double v) {
        PyObject* obj = PyFloat_FromDouble(v);
        return create(NODE_FLOAT, obj);
    }
    Node* NewBool(bool v) {
        PyObject* obj = newBool(v);
        return create(NODE_BOOL, obj);
    }
};

// toPy returns a Python object associated with a node.
// Returns a new reference.
PyObject* Node::toPy() {
    return ctx->toPy(this);
}

// lookupOrCreate either creates a new object or returns existing one.
// In the second case it creates a new reference.
Node* Node::lookupOrCreate(PyObject* obj) {
    return ctx->lookupOrCreate(obj);
}

// ==========================================
//          Python UAST iterator
// ==========================================

typedef struct {
  PyObject_HEAD
  Context *ctx;
  uast::Iterator<Node*> *iter;
  bool freeCtx;
} PyUastIter;

static void PyUastIter_dealloc(PyObject *self);

static PyObject *PyUastIter_iter(PyObject *self) {
  Py_INCREF(self);
  return self;
}

static PyObject *PyUastIter_next(PyObject *self) {
  auto it = (PyUastIter *)self;

  // TODO: check errors
  if (!it->iter->next()) {
    PyErr_SetNone(PyExc_StopIteration);
    return nullptr;
  }

  Node* node = it->iter->node();
  if (!node) Py_RETURN_NONE;

  return node->toPy(); // new ref
}

extern "C"
{
  static PyTypeObject PyUastIterType = {
    PyVarObject_HEAD_INIT(nullptr, 0)
    "pyuast.Iterator",              // tp_name
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

// ==========================================
//       Python UAST Context object
// ==========================================

class Context {
private:
    Interface *iface;
    uast::PtrInterface<Node*> *impl;
    uast::Context<Node*>   *ctx;

    // toPy returns a Python object associated with a node.
    // Returns a new reference.
    PyObject* toPy(Node* node) {
        if (node == nullptr) Py_RETURN_NONE;
        return iface->toPy(node);
    }
    // toNode returns a node associated with a Python object.
    // Creates a new reference.
    Node* toNode(PyObject* obj) {
        return iface->lookupOrCreate(obj);
    }
    PyObject* newIter(uast::Iterator<Node*> *it, bool freeCtx){
        PyUastIter *pyIt = PyObject_New(PyUastIter, &PyUastIterType);
        if (!pyIt)
          return nullptr;

        if (!PyObject_Init((PyObject *)pyIt, &PyUastIterType)) {
          Py_DECREF(pyIt);
          return nullptr;
        }
        pyIt->iter = it;
        pyIt->ctx = this;
        pyIt->freeCtx = freeCtx;
        return (PyObject*)pyIt;
    }
public:
    Context(){
        // create a class that makes and tracks UAST nodes
        iface = new Interface();
        // create an implementation that will handle libuast calls
        impl = new uast::PtrInterface<Node*>(iface);
        // create a new UAST context based on this implementation
        ctx = impl->NewContext();
    }
    ~Context(){
        delete(ctx);
        delete(impl);
        delete(iface);
    }

    // RootNode returns a root UAST node, if set.
    // Returns a new reference.
    PyObject* RootNode(){
        Node* root = ctx->RootNode();
        return toPy(root); // new ref
    }

    // Iterate enumerates UAST nodes in a specified order.
    // Creates a new reference.
    PyObject* Iterate(PyObject* node, TreeOrder order, bool freeCtx){
        Node* unode = toNode(node);
        auto iter = ctx->Iterate(unode, order);
        return newIter(iter, freeCtx);
    }

    // Filter queries UAST.
    // Creates a new reference.
    PyObject* Filter(PyObject* node, std::string query){
        Node* unode = toNode(node);
        if (unode == nullptr) {
          unode = ctx->RootNode();
        }

        auto it = ctx->Filter(unode, query);
        return newIter(it, false);
    }
    // Encode serializes UAST.
    // Creates a new reference.
    PyObject* Encode(PyObject *node, UastFormat format) {
        uast::Buffer data = ctx->Encode(toNode(node), format);
        return asPyBuffer(data); // TODO: this probably won't deallocate the buffer
    }
    PyObject* LoadFrom(PyNodeExt *src) {
        auto sctx = src->ctx->ctx;
        NodeHandle snode = src->handle;

        Node* node = uast::Load(sctx, snode, ctx);
        return toPy(node); // new ref
    }
};

static PyObject *PyNodeExt_load(PyNodeExt *self, PyObject *Py_UNUSED(ignored)) {
    auto ctx = new Context();
    PyObject* node = ctx->LoadFrom(self);
    delete(ctx);
    return node;
}

static void PyUastIter_dealloc(PyObject *self) {
  auto it = (PyUastIter *)self;
  delete(it->iter);

  if (it->freeCtx && it->ctx) {
    delete(it->ctx);
  }
  it->freeCtx = false;
  it->ctx = nullptr;
}

typedef struct {
  PyObject_HEAD
  Context *p;
} PyUast;

static void PyUast_dealloc(PyObject *self) {
  delete(((PyUast *)self)->p);
  // TODO: delete self?
}

static PyObject *PyUast_root(PyUast *self, PyObject *Py_UNUSED(ignored)) {
    return self->p->RootNode();
}

static PyObject *PyUast_filter(PyUast *self, PyObject *args) {
    PyObject *node = nullptr;
    char *query = nullptr;
    if (!PyArg_ParseTuple(args, "Os", &node, &query))
      return nullptr;
    return self->p->Filter(node, query);
}

static PyObject *PyUast_encode(PyUast *self, PyObject *args) {
    PyObject *node = nullptr;
    UastFormat format = UAST_BINARY; // TODO: make it a kwarg and enum
    if (!PyArg_ParseTuple(args, "Oi", &node, &format))
      return nullptr;
    return self->p->Encode(node, format);
}

static PyMethodDef PyUast_methods[] = {
    {"root", (PyCFunction) PyUast_root, METH_NOARGS,
     "Return the root node attached to this query context"
    },
    {"filter", (PyCFunction) PyUast_filter, METH_VARARGS,
     "Filter a provided UAST with XPath"
    },
    {"encode", (PyCFunction) PyUast_encode, METH_VARARGS,
     "Encodes a UAST into a buffer"
    },
    {nullptr}  // Sentinel
};

extern "C"
{
  static PyTypeObject PyUastType = {
      PyVarObject_HEAD_INIT(nullptr, 0)
      "pyuast.Context",               // tp_name
      sizeof(PyUast),                 // tp_basicsize
      0,                              // tp_itemsize
      PyUast_dealloc,                 // tp_dealloc
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
      "Internal Context object",      // tp_doc
      0,                              // tp_traverse
      0,                              // tp_clear
      0,                              // tp_richcompare
      0,                              // tp_weaklistoffset
      0,                              // tp_iter: __iter()__ method
      0,                              // tp_iternext: next() method
      PyUast_methods,                 // tp_methods
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

// ==========================================
//            Global functions
// ==========================================

static PyObject *PyUastIter_new(PyObject *self, PyObject *args) {
  PyObject *obj = nullptr;
  uint8_t order;

  if (!PyArg_ParseTuple(args, "OB", &obj, &order))
    return nullptr;

  // the node can either be external or any other Python object
  if (PyObject_TypeCheck(obj, &PyNodeExtType)) {
    // external node -> external iterator
    auto node = (PyNodeExt*)obj;
    return node->ctx->Iterate(obj, (TreeOrder)order);
  }
  // Python object -> create a new context and attach it to an iterator
  Context* ctx = new Context();
  return ctx->Iterate(obj, (TreeOrder)order, true);
}

static PyObject *PyUastDecode(PyObject *self, PyObject *args) {
    PyObject *obj = nullptr;
    UastFormat format = UAST_BINARY; // TODO: make it a kwarg

    if (!PyArg_ParseTuple(args, "Oi", &obj, &format))
      return nullptr;

    Py_buffer buf;

    int res = PyObject_GetBuffer(obj, &buf, PyBUF_C_CONTIGUOUS);
    if (res != 0)
        return nullptr;

    uast::Buffer ubuf(buf.buf, (size_t)(buf.len));

    uast::Context<NodeHandle>* ctx = uast::Decode(ubuf, format);
    PyBuffer_Release(&buf);

    PyContextExt *pyU = PyObject_New(PyContextExt, &PyContextExtType);
    if (!pyU) {
      delete(ctx);
      return nullptr;
    }
    pyU->p = new ContextExt(ctx);
    return (PyObject*)pyU;
}

static PyObject *PyUast_new(PyObject *self, PyObject *args) {
    if (!PyArg_ParseTuple(args, "")) {
      return nullptr;
    }

    PyUast *pyU = PyObject_New(PyUast, &PyUastType);
    if (!pyU) {
      return nullptr;
    }
    pyU->p = new Context();
    return (PyObject*)pyU;
}

static PyMethodDef extension_methods[] = {
    {"iterator", PyUastIter_new, METH_VARARGS, "Get an iterator over a node"},
    {"decode", PyUastDecode, METH_VARARGS, "Decode UAST from a byte array"},
    {"uast", PyUast_new, METH_VARARGS, "Creates a new UAST context"},
    {nullptr, nullptr, 0, nullptr}
};

static struct PyModuleDef module_def = {
    PyModuleDef_HEAD_INIT,
    "pyuast",
    nullptr,
    -1,
    extension_methods,
    nullptr,
    nullptr,
    nullptr,
    nullptr
};

PyMODINIT_FUNC
PyInit_pyuast(void)
{
  if (PyType_Ready(&PyContextExtType) < 0) return nullptr;
  if (PyType_Ready(&PyNodeExtType) < 0) return nullptr;
  if (PyType_Ready(&PyUastIterExtType) < 0) return nullptr;

  if (PyType_Ready(&PyUastType) < 0) return nullptr;
  if (PyType_Ready(&PyUastIterType) < 0) return nullptr;
  return PyModule_Create(&module_def);
}
