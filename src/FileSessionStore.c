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
#include "utils.h"
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
    assert(tempdir[strlen(tempdir)-1] == '/'); // see smisk_FileSessionStore_read()
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
  // XXX check so that self->dir exits
  return 0;
}


void smisk_FileSessionStore_dealloc(smisk_FileSessionStore* self) {
  log_debug("ENTER smisk_FileSessionStore_dealloc");
  Py_DECREF(self->dir);
  Py_DECREF(self->file_prefix);
}

#pragma mark -
#pragma mark Methods


PyObject *file_readall(const char *fn) {
  log_debug("ENTER file_readall  fn='%s'", fn);
  FILE *f;
  PyObject *py_buf;
  char *buf, *p;
  size_t br, length = 0, chunksize = 8096;
  size_t bufsize = chunksize;
  
  if( (py_buf = PyString_FromStringAndSize(NULL, bufsize)) == NULL ) {
    return NULL;
  }
  
  buf = PyString_AS_STRING(py_buf);
  
  if((f = fopen(fn, "r")) == NULL) {
    Py_DECREF(py_buf);
    PyErr_SetFromErrnoWithFilename(PyExc_IOError, __FILE__);
    return NULL;
  }
  
  p = buf;
  
  while( (br = fread(p, 1, chunksize, f)) ) {
    length += br;
    p += br;
    if(br < chunksize) {
      // EOF
      break;
    }
    // Realloc
    bufsize += chunksize;
    if(_PyString_Resize(&py_buf, (Py_ssize_t)bufsize) != 0) {
      Py_DECREF(py_buf);
      fclose(f);
      return NULL;
    }
  }
  
  fclose(f);
  buf[length] = 0;
  ((PyStringObject *)py_buf)->ob_size = length;
  return py_buf;
}


PyDoc_STRVAR(smisk_FileSessionStore_read_DOC,
  ":param  session_id: Session ID\n"
  ":type   session_id: string\n"
  ":rtype: object");
PyObject* smisk_FileSessionStore_read(smisk_FileSessionStore* self, PyObject* session_id) {
  log_debug("ENTER smisk_FileSessionStore_read");
  PyObject *fn, *data;
  
  if(!PyString_Check(session_id)) {
    return NULL;
  }
  log_debug("session_id='%s'", PyString_AS_STRING(session_id));
  
  fn = PyString_FromStringAndSize("", 0);
  PyString_Concat(&fn, self->dir);
  if(PyString_AS_STRING(fn)[PyString_GET_SIZE(fn)-1] != '/') {
    PyString_ConcatAndDel(&fn, PyString_FromStringAndSize("/", 1));
  }
  PyString_Concat(&fn, self->file_prefix);
  PyString_Concat(&fn, session_id);
  
  // Read file data
  if(file_exist(PyString_AS_STRING(fn))) {
    if( (data = file_readall(PyString_AS_STRING(fn))) == NULL ) {
      Py_DECREF(fn);
      return NULL;
    }
    // XXX unarchive
    Py_DECREF(fn);
    return data; // Give away our reference to receiver
  }
  
  log_debug("No session data  fn='%s'", PyString_AS_STRING(fn));
  Py_DECREF(fn);
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
