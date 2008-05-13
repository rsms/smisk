/*
Copyright (c) 2007-2008 Rasmus Andersson and contributors

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
#include "__init__.h"
#include "utils.h"
#include "file.h"
#include "SessionStore.h"

#include <structmember.h>


#pragma mark Initialization & deallocation

PyObject *smisk_SessionStore_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {
  log_debug("ENTER smisk_SessionStore_new");
  smisk_SessionStore *self;
  
  if ( (self = (smisk_SessionStore *)type->tp_alloc(type, 0)) == NULL ) {
    return NULL;
  }
  
  self->ttl = 900;
  self->name = PyString_FromString("SID");
  
  return (PyObject *)self;
}


int smisk_SessionStore_init(smisk_SessionStore *self, PyObject* args, PyObject* kwargs) {  
  return 0;
}


void smisk_SessionStore_dealloc(smisk_SessionStore *self) {
  log_debug("ENTER smisk_SessionStore_dealloc");
  Py_DECREF(self->name);
  self->ob_type->tp_free((PyObject*)self);
  log_debug("EXIT smisk_SessionStore_dealloc");
}

#pragma mark -
#pragma mark Methods


PyDoc_STRVAR(smisk_SessionStore_read_DOC,
  ":param  session_id: Session ID\n"
  ":type   session_id: string\n"
  ":rtype: object");
PyObject* smisk_SessionStore_read(smisk_SessionStore *self, PyObject* session_id) {
  PyErr_SetString(PyExc_NotImplementedError, "read");
  return NULL;
}


PyDoc_STRVAR(smisk_SessionStore_write_DOC,
  ":param  session_id: Session ID\n"
  ":type   session_id: string\n"
  ":param  data:       Data to be associated with ``session_id``\n"
  ":type   data:       object\n"
  ":rtype: None");
PyObject* smisk_SessionStore_write(smisk_SessionStore *self, PyObject* args) {
  PyErr_SetString(PyExc_NotImplementedError, "write");
  return NULL;
}


PyDoc_STRVAR(smisk_SessionStore_refresh_DOC,
  ":param  session_id: Session ID\n"
  ":type   session_id: string\n"
  ":rtype: None");
PyObject* smisk_SessionStore_refresh(smisk_SessionStore *self, PyObject* session_id) {
  PyErr_SetString(PyExc_NotImplementedError, "refresh");
  return NULL;
}


PyDoc_STRVAR(smisk_SessionStore_destroy_DOC,
  ":param  session_id: Session ID\n"
  ":type   session_id: string\n"
  ":rtype: None");
PyObject* smisk_SessionStore_destroy(smisk_SessionStore *self, PyObject* session_id) {
  PyErr_SetString(PyExc_NotImplementedError, "destroy");
  return NULL;
}


#pragma mark -
#pragma mark Type construction

PyDoc_STRVAR(smisk_SessionStore_DOC,
  "Basic session store type");

// Methods
static PyMethodDef smisk_SessionStore_methods[] = {
  {"read", (PyCFunction)smisk_SessionStore_read, METH_O, smisk_SessionStore_read_DOC},
  {"write", (PyCFunction)smisk_SessionStore_write, METH_VARARGS, smisk_SessionStore_write_DOC},
  {"refresh", (PyCFunction)smisk_SessionStore_refresh, METH_O, smisk_SessionStore_refresh_DOC},
  {"destroy", (PyCFunction)smisk_SessionStore_destroy, METH_O, smisk_SessionStore_destroy_DOC},
  {NULL, NULL, 0, NULL}
};

// Class members
static struct PyMemberDef smisk_SessionStore_members[] = {
  {"ttl", T_INT, offsetof(smisk_SessionStore, ttl), 0,
    ":type: int\n\n"
    "For how long a session should be valid, expressed in seconds. Defaults to 900."},
  
  {"name", T_OBJECT_EX, offsetof(smisk_SessionStore, name), 0,
    ":type: string\n\n"
    "Name used to identify the session id cookie. Defaults to \"SID\""},
  
  {NULL, 0, NULL, 0, NULL}
};

// Type definition
PyTypeObject smisk_SessionStoreType = {
  PyObject_HEAD_INIT(&PyType_Type)
  0,                         /*ob_size*/
  "smisk.core.SessionStore",  /*tp_name*/
  sizeof(smisk_SessionStore), /*tp_basicsize*/
  0,                         /*tp_itemsize*/
  (destructor)smisk_SessionStore_dealloc,        /* tp_dealloc */
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
  smisk_SessionStore_DOC,          /*tp_doc*/
  (traverseproc)0,           /* tp_traverse */
  0,                         /* tp_clear */
  0,                         /* tp_richcompare */
  0,                         /* tp_weaklistoffset */
  0,                         /* tp_iter */
  0,                         /* tp_iternext */
  smisk_SessionStore_methods, /* tp_methods */
  smisk_SessionStore_members, /* tp_members */
  0,                              /* tp_getset */
  0,                           /* tp_base */
  0,                           /* tp_dict */
  0,                           /* tp_descr_get */
  0,                           /* tp_descr_set */
  0,                           /* tp_dictoffset */
  (initproc)smisk_SessionStore_init, /* tp_init */
  0,                           /* tp_alloc */
  smisk_SessionStore_new,  /* tp_new */
  0                            /* tp_free */
};

int smisk_SessionStore_register_types(PyObject *module) {
  if(PyType_Ready(&smisk_SessionStoreType) == 0) {
    return PyModule_AddObject(module, "SessionStore", (PyObject *)&smisk_SessionStoreType);
  }
  return -1;
}
