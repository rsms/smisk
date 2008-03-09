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
#include "__init__.h"
#include "utils.h"
#include "FileSessionStore.h"
#include <structmember.h>
#include <sys/time.h>
#include <fcntl.h>
#include <marshal.h>

#pragma mark Internal


static FILE *_open_exclusive(const char *filename) {
  log_debug("_open_exclusive(\"%s\")", filename);
#if defined(O_EXCL)&&defined(O_CREAT)&&defined(O_WRONLY)&&defined(O_TRUNC)
	/* Use O_EXCL to avoid a race condition when another process tries to
	   write the same file.  When that happens, our open() call fails,
	   which is just fine (since it's only a cache).
	   XXX If the file exists and is writable but the directory is not
	   writable, the file will never be written.  Oh well.
	*/
	int fd;
	(void) unlink(filename);
	fd = open(filename, O_EXCL|O_CREAT|O_WRONLY|O_TRUNC
#ifdef O_BINARY
				|O_BINARY   /* necessary for Windows */
#endif
#ifdef __VMS
                        , 0666, "ctxt=bin", "shr=nil"
#else
                        , 0666
#endif
		  );
	if (fd < 0)
		return NULL;
	return fdopen(fd, "wb");
#else
	/* Best we can do -- on Windows this can't happen anyway */
	return fopen(filename, "wb");
#endif
}



#pragma mark Initialization & deallocation

static PyObject *tempfile_mod = NULL;


static PyObject *smisk_FileSessionStore_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {
  log_debug("ENTER smisk_FileSessionStore_new");
  smisk_FileSessionStore *self;
  PyObject *s;
  
  if ( (self = (smisk_FileSessionStore *)type->tp_alloc(type, 0)) == NULL ) {
    return NULL;
  }
  
  // Load required modules
  if(tempfile_mod == NULL) {
    // tempfile
    s = PyString_FromString("tempfile");
    tempfile_mod = PyImport_Import(s);
    Py_DECREF(s);
    if(tempfile_mod == NULL) {
      tempfile_mod = Py_None;
    }
  }
  
  if(tempfile_mod != Py_None) {
    if( (self->file_prefix = PyObject_CallMethod(tempfile_mod, "gettempdir", NULL)) == NULL ) {
      log_debug("PyObject_CallMethod failed");
      Py_DECREF(self);
      return NULL;
    }
    PyString_ConcatAndDel(&self->file_prefix, PyString_FromString("/smisk-sess."));
    if(self->file_prefix == NULL) {
      log_debug("PyString_ConcatAndDel failed");
      Py_DECREF(self);
      return NULL;
    }
  }
  else {
    self->file_prefix = PyString_FromString("/tmp/smisk-sess.");
  }
  
  return (PyObject *)self;
}


int smisk_FileSessionStore_init(smisk_FileSessionStore* self, PyObject* args, PyObject* kwargs) {
  // XXX check so that self->dir exits
  return 0;
}


void smisk_FileSessionStore_dealloc(smisk_FileSessionStore* self) {
  log_debug("ENTER smisk_FileSessionStore_dealloc");
  Py_DECREF(self->file_prefix);
}

#pragma mark -
#pragma mark Methods


PyDoc_STRVAR(smisk_FileSessionStore_path_DOC,
  ":param  session_id: Session ID\n"
  ":type   session_id: string\n"
  ":rtype: string");
static PyObject *smisk_FileSessionStore_path(smisk_FileSessionStore* self, PyObject* session_id) {
  PyObject *fn;
  fn = PyString_FromStringAndSize(PyString_AS_STRING(self->file_prefix), PyString_GET_SIZE(self->file_prefix));
  if(fn == NULL) {
    return NULL;
  }
  PyString_Concat(&fn, session_id);
  return fn;
}


PyDoc_STRVAR(smisk_FileSessionStore_read_DOC,
  ":param  session_id: Session ID\n"
  ":type   session_id: string\n"
  ":rtype: object");
PyObject* smisk_FileSessionStore_read(smisk_FileSessionStore* self, PyObject* session_id) {
  log_debug("ENTER smisk_FileSessionStore_read");
  PyObject *fn, *data;
  char *pathname;
  FILE *fp;
  
  if(!PyString_Check(session_id)) {
    return NULL;
  }
  
  if( (fn = smisk_FileSessionStore_path(self, session_id)) == NULL ) {
    return NULL;
  }
  
  pathname = PyString_AS_STRING(fn);
  
  // Read file data
  if(file_exist(pathname)) {
    if( (fp = fopen(pathname, "rb")) == NULL ) {
      Py_DECREF(fn);
      PyErr_SetFromErrnoWithFilename(PyExc_IOError, __FILE__);
      return NULL;
    }
    
    if( (data = PyMarshal_ReadObjectFromFile(fp)) == NULL ) {
      fclose(fp);
      Py_DECREF(fn);
      return NULL;
    }
    
    fclose(fp);
    log_debug("Read session data from %s", pathname);
    Py_DECREF(fn);
    return data; // Give away our reference to receiver
  }
  else {
    log_debug("No session data. File not found '%s'", PyString_AS_STRING(fn));
    Py_DECREF(fn);
    Py_RETURN_NONE;
  }
}


PyDoc_STRVAR(smisk_FileSessionStore_write_DOC,
  ":param  session_id: Session ID\n"
  ":type   session_id: string\n"
  ":param  data:       Data to be associated with ``session_id``\n"
  ":type   data:       object\n"
  ":rtype: None");
PyObject* smisk_FileSessionStore_write(smisk_FileSessionStore* self, PyObject* args) {
  log_debug("ENTER smisk_FileSessionStore_write");
  PyObject *session_id, *data, *fn;
  char *pathname;
  FILE *fp;
  
  if( PyTuple_GET_SIZE(args) != 2 ) {
    PyErr_Format(PyExc_TypeError, "this method takes exactly 2 arguments");
    return NULL;
  }
  
  if( (session_id = PyTuple_GET_ITEM(args, 0)) == NULL ) {
    return NULL;
  }
  
  if( (data = PyTuple_GET_ITEM(args, 1)) == NULL ) {
    return NULL;
  }
  
  if( (fn = smisk_FileSessionStore_path(self, session_id)) == NULL ) {
    return NULL;
  }
  
  pathname = PyString_AS_STRING(fn);
  
  fp = _open_exclusive(pathname);
  if(fp == NULL) {
    PyErr_SetFromErrnoWithFilename(PyExc_IOError, __FILE__);
    return NULL;
  }
  
  PyMarshal_WriteObjectToFile(data, fp, Py_MARSHAL_VERSION);
  if ((fflush(fp) != 0) || ferror(fp)) {
    PyErr_SetFromErrnoWithFilename(PyExc_IOError, __FILE__);
		log_error("can't write to %s", pathname);
		fclose(fp);
		(void) unlink(pathname);
		return NULL;
	}
	
	fclose(fp);
  log_debug("Wrote '%s'", pathname);
  
  Py_DECREF(fn);
  Py_RETURN_NONE;
}


PyDoc_STRVAR(smisk_FileSessionStore_refresh_DOC,
  ":param  session_id: Session ID\n"
  ":type   session_id: string\n"
  ":rtype: None");
PyObject* smisk_FileSessionStore_refresh(smisk_FileSessionStore* self, PyObject* session_id) {
  log_debug("ENTER smisk_FileSessionStore_refresh %s", PyString_AS_STRING(session_id));
  PyObject *fn;
  
  if( (fn = smisk_FileSessionStore_path(self, session_id)) == NULL ) {
    return NULL;
  }
  
  if(utimes(PyString_AS_STRING(fn), NULL) != 0) {
    log_debug("utimes() failed - '%s' probably don't exist", PyString_AS_STRING(fn));
  }
  
  Py_DECREF(fn);
  Py_RETURN_NONE;
}


PyDoc_STRVAR(smisk_FileSessionStore_destroy_DOC,
  ":param  session_id: Session ID\n"
  ":type   session_id: string\n"
  ":rtype: None");
PyObject* smisk_FileSessionStore_destroy(smisk_FileSessionStore* self, PyObject* session_id) {
  log_debug("ENTER smisk_FileSessionStore_destroy");
  PyObject *fn;
  char *p;
  
  if( (fn = smisk_FileSessionStore_path(self, session_id)) == NULL ) {
    return NULL;
  }
  
  p = PyString_AS_STRING(fn);
  
  if(file_exist(p) && (unlink(p) != 0)) {
    PyErr_SetFromErrnoWithFilename(PyExc_IOError, __FILE__);
    Py_DECREF(fn);
    return NULL;
  }
  
  Py_DECREF(fn);
  Py_RETURN_NONE;
}


PyDoc_STRVAR(smisk_FileSessionStore_gc_DOC,
  ":param  ttl: Max lifetime in seconds\n"
  ":type   ttl: int\n"
  ":rtype: None");
PyObject* smisk_FileSessionStore_gc(smisk_FileSessionStore* self, PyObject* ttl) {
  log_debug("ENTER smisk_FileSessionStore_gc");
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
  {"refresh", (PyCFunction)smisk_FileSessionStore_refresh, METH_O, smisk_FileSessionStore_refresh_DOC},
  {"destroy", (PyCFunction)smisk_FileSessionStore_destroy, METH_O, smisk_FileSessionStore_destroy_DOC},
  {"gc", (PyCFunction)smisk_FileSessionStore_gc, METH_O, smisk_FileSessionStore_gc_DOC},
  {"path", (PyCFunction)smisk_FileSessionStore_path, METH_O, smisk_FileSessionStore_path_DOC},
  {NULL}
};

// Class members
static struct PyMemberDef smisk_FileSessionStore_members[] = {
  {"file_prefix", T_OBJECT_EX, offsetof(smisk_FileSessionStore, file_prefix), 0,
    ":type: string\n\n"
    "A string to prepend to each file stored in `dir`.\n"
    "\n"
    "Defaults to ´´tempfile.tempdir + \"smisk-sess.\"`` - for example: ``/tmp/smisk-sess.``"},
  
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
