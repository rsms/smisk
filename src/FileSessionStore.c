/*
Copyright (c) 2007, Rasmus Andersson

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
*/
#include "module.h"
#include "FileSessionStore.h"
#include <structmember.h>

#pragma mark Initialization & deallocation


static PyObject *smisk_FileSessionStore_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {
  log_debug("ENTER smisk_FileSessionStore_new");
  smisk_FileSessionStore *self;
  
  self = (smisk_FileSessionStore *)type->tp_alloc(type, 0);
  if (self != NULL) {
    char *tempdir = getenv("TMPDIR");
    if(tempdir == NULL) {
      tempdir = "/tmp/";
    }
    if( (self->dir = PyString_FromString(tempdir)) == NULL ) {
      Py_DECREF(self);
      return NULL;
    }
    if( (self->file_prefix = PyString_FromString("smisk-sess.")) == NULL ) {
      Py_DECREF(self);
      return NULL;
    }
  }
  
  return (PyObject *)self;
}

int smisk_FileSessionStore_init(smisk_FileSessionStore* self, PyObject* args, PyObject* kwargs) {
  log_debug("ENTER smisk_FileSessionStore_init");
  return 0;
}


void smisk_FileSessionStore_dealloc(smisk_FileSessionStore* self) {
  log_debug("ENTER smisk_FileSessionStore_dealloc");
  Py_DECREF(self->dir);
  Py_DECREF(self->file_prefix);
}

#pragma mark -
#pragma mark Methods

PyDoc_STRVAR(smisk_FileSessionStore_read_DOC,
  "\n"
  "\n"
  ":param  session_id: Session ID\n"
  ":type   session_id: string\n"
  ":rtype: object");
PyObject* smisk_FileSessionStore_read(smisk_FileSessionStore* self, PyObject* session_id) {
  Py_RETURN_NONE;
}


PyDoc_STRVAR(smisk_FileSessionStore_write_DOC,
  ":param  session_id: Session ID\n"
  ":type   session_id: string\n"
  ":param  data:       Data to be associated with ``session_id``\n"
  ":type   data:       object\n"
  ":rtype: None");
PyObject* smisk_FileSessionStore_write(smisk_FileSessionStore* self, PyObject* args) {
  Py_RETURN_NONE;
}


PyDoc_STRVAR(smisk_FileSessionStore_destroy_DOC,
  ":param  session_id: Session ID\n"
  ":type   session_id: string\n"
  ":rtype: None");
PyObject* smisk_FileSessionStore_destroy(smisk_FileSessionStore* self, PyObject* session_id) {
  Py_RETURN_NONE;
}


PyDoc_STRVAR(smisk_FileSessionStore_gc_DOC,
  ":param  ttl: Max lifetime in seconds\n"
  ":type   ttl: int\n"
  ":rtype: None");
PyObject* smisk_FileSessionStore_gc(smisk_FileSessionStore* self, PyObject* ttl) {
  Py_RETURN_NONE;
}


#pragma mark -
#pragma mark Type construction

PyDoc_STRVAR(smisk_FileSessionStore_DOC,
  "Basic session store which uses files");

// Methods
static PyMethodDef smisk_FileSessionStore_methods[] = {
  {"read", (PyCFunction)smisk_FileSessionStore_read, METH_O, smisk_FileSessionStore_read_DOC},
  {"write", (PyCFunction)smisk_FileSessionStore_write, METH_VARARGS, smisk_FileSessionStore_write_DOC},
  {"destroy", (PyCFunction)smisk_FileSessionStore_destroy, METH_O, smisk_FileSessionStore_destroy_DOC},
  {"gc", (PyCFunction)smisk_FileSessionStore_gc, METH_O, smisk_FileSessionStore_gc_DOC},
  {NULL}
};

// Class members
static struct PyMemberDef smisk_FileSessionStore_members[] = {
  {"dir", T_OBJECT_EX, offsetof(smisk_FileSessionStore, dir), 0,
    ":type: string\n\n"
    "Directory in which to store session data files.\n"
    "\n"
    "Defaults to the value of the *TMPDIR* environment variable."},
  
  {"file_prefix", T_OBJECT_EX, offsetof(smisk_FileSessionStore, file_prefix), 0,
    ":type: string\n\n"
    "A string to prepend to each file stored in `dir`.\n"
    "\n"
    "Defaults to \"``smisk-sess.``\"."},
  
  {NULL}
};

// Type definition
PyTypeObject smisk_FileSessionStoreType = {
  PyObject_HEAD_INIT(&PyType_Type)
  0,                         /*ob_size*/
  "smisk.core.FileSessionStore",  /*tp_name*/
  sizeof(smisk_FileSessionStore), /*tp_basicsize*/
  0,                         /*tp_itemsize*/
  (destructor)smisk_FileSessionStore_dealloc,        /* tp_dealloc */
  0,                         /*tp_print*/
  0,                         /*tp_getattr*/
  0,                         /*tp_setattr*/
  0,                         /*tp_compare*/
  0,                         /*tp_repr*/
  0,                         /*tp_as_number*/
  0,                         /*tp_as_sequence*/
  0,                         /*tp_as_mapping*/
  0,                         /*tp_hash */
  0,                         /*tp_call*/
  0,                         /*tp_str*/
  0,                         /*tp_getattro*/
  0,                         /*tp_setattro*/
  0,                         /*tp_as_buffer*/
  Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE, /*tp_flags*/
  smisk_FileSessionStore_DOC,          /*tp_doc*/
  (traverseproc)0,           /* tp_traverse */
  0,                         /* tp_clear */
  0,                         /* tp_richcompare */
  0,                         /* tp_weaklistoffset */
  0,                         /* tp_iter */
  0,                         /* tp_iternext */
  smisk_FileSessionStore_methods, /* tp_methods */
  smisk_FileSessionStore_members, /* tp_members */
  0,                              /* tp_getset */
  0,                           /* tp_base */
  0,                           /* tp_dict */
  0,                           /* tp_descr_get */
  0,                           /* tp_descr_set */
  0,                           /* tp_dictoffset */
  (initproc)smisk_FileSessionStore_init, /* tp_init */
  0,                           /* tp_alloc */
  smisk_FileSessionStore_new,  /* tp_new */
  0                            /* tp_free */
};

int smisk_FileSessionStore_register_types(PyObject *module) {
  if(PyType_Ready(&smisk_FileSessionStoreType) == 0) {
    return PyModule_AddObject(module, "FileSessionStore", (PyObject *)&smisk_FileSessionStoreType);
  }
  return -1;
}
