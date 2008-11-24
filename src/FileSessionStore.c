/*
Copyright (c) 2007-2008 Rasmus Andersson

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
#include "FileSessionStore.h"

#include <dirent.h>
#if HAVE_FCNTL_H
  #include <fcntl.h>
#endif

#include <structmember.h>
#include <marshal.h>
#include <pythread.h>
#include <stdlib.h>


#pragma mark Internal

// "returns" 0 on success or -1 on failure when an error has been set
static int _unlink(char *fn) {
  if (unlink((const char *)fn) != 0) {
    PyErr_SET_FROM_ERRNO;
    return -1;
  }
  return 0;
}


static time_t _is_garbage(smisk_FileSessionStore *self, const char *fn, int fd) {
  time_t n, m;
  m = smisk_file_mtime(fn, fd);
  if (m == 0)
    return 0;
  n = time(NULL) - m;
  return ( n > ((smisk_SessionStore *)self)->ttl ) ? n : 0;
}


static int _gc_run(void *_self) {
  log_trace("ENTER");
  // XXX Some non-windows compliant code here.
  //     ...but who cares about Windows anyway?
  DIR *d;
  struct dirent *f;
  char *p, *path_p, *fn_prefix, *path_buf;
  size_t fn_prefix_len, path_p_len;
  smisk_FileSessionStore *self = (smisk_FileSessionStore *)_self;
  
  path_p = PyString_AsString(self->file_prefix);
  p = strrchr(path_p, '/');
  fn_prefix = p+1;
  fn_prefix_len = strlen(fn_prefix);
  
  if (p) {
    EXTERN_OP_START;
    *p = '\0';
    d = opendir(path_p);
    if (d) {
      path_p_len = strlen(path_p);
      path_buf = (char *)malloc(path_p_len + 1 + PATH_MAX + 1);
      strcpy(path_buf, path_p);
      path_buf[path_p_len] = '/';
      path_buf[path_p_len+1] = 0;
      
      while ((f = readdir(d)) != NULL) {
        if ( (f->d_type == DT_REG)
          && (strncmp(f->d_name, fn_prefix, min(strlen(f->d_name), fn_prefix_len)) == 0) )
        {
          strcpy(path_buf+path_p_len+1, f->d_name);
          if (_is_garbage(self, path_buf, -1)) {
            #if SMISK_DEBUG
              log_debug("unlink %s %s", path_buf, (unlink(path_buf) == 0) ? "SUCCESS" : "FAILED");
            #else
              unlink(path_buf);
            #endif
          }
        }
      }
      free(path_buf);
      closedir(d);
    }
    #if SMISK_DEBUG
      else {
        *p = '\0';
        log_error("Failed to opendir(\"%s\")", path_p);
      }
    #endif
    EXTERN_OP_END;
    *p = '/';
  }
  
  return 0;
}


#pragma mark Initialization & deallocation

static PyObject *tempfile_mod = NULL;


int smisk_FileSessionStore_init(smisk_FileSessionStore *self, PyObject *args, PyObject *kwargs) {
  log_trace("ENTER");
  
  // Load tempfile module
  if (tempfile_mod == NULL) {
    tempfile_mod = PyImport_ImportModule("tempfile");
    if (tempfile_mod == NULL)
      tempfile_mod = Py_None;
  }
  
  if (tempfile_mod != Py_None) {
    if ( (self->file_prefix = PyObject_CallMethod(tempfile_mod, "gettempdir", NULL)) == NULL ) {
      log_debug("PyObject_CallMethod failed");
      Py_DECREF((PyObject *)self);
      return -1;
    }
    PyString_ConcatAndDel(&self->file_prefix, PyString_FromString("/smisk-sess."));
    if (self->file_prefix == NULL) {
      log_debug("PyString_ConcatAndDel failed");
      Py_DECREF((PyObject *)self);
      return -1;
    }
  }
  else {
    self->file_prefix = PyString_FromString("/tmp/smisk-sess.");
  }
  
  self->gc_probability = 0.1;
  
  return 0;
}


void smisk_FileSessionStore_dealloc(smisk_FileSessionStore *self) {
  log_trace("ENTER");
  
  Py_DECREF(self->file_prefix);
  ((smisk_SessionStore *)self)->ob_type->tp_base->tp_dealloc((PyObject *)self);
  
  log_debug("EXIT smisk_FileSessionStore_dealloc");
}

#pragma mark -
#pragma mark Methods


PyDoc_STRVAR(smisk_FileSessionStore_path_DOC,
  ":param  session_id: Session ID\n"
  ":type   session_id: string\n"
  ":rtype: string");
static PyObject *smisk_FileSessionStore_path(smisk_FileSessionStore *self, PyObject *session_id) {
  log_trace("ENTER");
  PyObject *fn;
  
  fn = PyObject_Str(self->file_prefix);
  
  if (fn)
    PyString_Concat(&fn, session_id);
  
  return fn;
}


PyDoc_STRVAR(smisk_FileSessionStore_read_DOC,
  ":param  session_id: Session ID\n"
  ":type   session_id: string\n"
  ":raises smisk.core.InvalidSessionError: if there is no actual session associated with ``session_id``.\n"
  ":rtype: object");
PyObject *smisk_FileSessionStore_read(smisk_FileSessionStore *self, PyObject *session_id) {
  log_trace("ENTER");
  PyObject *fn, *data = NULL;
  char *pathname;
  FILE *fp = NULL;
  
  if (probably_call(self->gc_probability, _gc_run, (void *)self) == -1)
    return NULL;
  
  if ( !SMISK_PyString_Check(session_id) ) {
    PyErr_SetString(PyExc_TypeError, "session_id must be a string");
    return NULL;
  }
  
  if ( (fn = smisk_FileSessionStore_path(self, session_id)) == NULL )
    return NULL;
  
  pathname = PyString_AsString(fn);
  
  // Read file data
  if (smisk_file_exist(pathname)) {
    if ( _is_garbage(self, pathname, -1) ) {
      log_debug("Garbage session %s (older than ttl=%d)",
                PyString_AsString(session_id),
                ((smisk_SessionStore *)self)->ttl);
      
      if (_unlink(pathname) != 0)
        PyErr_SET_FROM_ERRNO;
      else
        PyErr_SetString(smisk_InvalidSessionError, "data too old");
    }
    else {
      if ( (fp = fopen(pathname, "rb")) == NULL ) {
        PyErr_SET_FROM_ERRNO;
        goto end_return;
      }
      
      if (smisk_file_lock(fp, SMISK_FILE_LOCK_SHARED) != 0) {
        PyErr_SET_FROM_ERRNO;
        goto end_return;
      }
      
      data = PyMarshal_ReadObjectFromFile(fp);
      
      IFDEBUG(if (data) log_debug("Successfully read session data from %s", pathname));
      
      if (smisk_file_unlock(fp) != 0) {
        PyErr_SET_FROM_ERRNO;
        log_debug("Failed to unlock file opened from %s", pathname);
        goto end_return;
      }
    }
  }
  else {
    log_debug("No session data. File not found '%s'", PyString_AsString(fn));
    PyErr_SetString(smisk_InvalidSessionError, "no data");
  }
  
end_return:
  if (fp)
    fclose(fp);
  Py_DECREF(fn);
  return data;
}


PyDoc_STRVAR(smisk_FileSessionStore_write_DOC,
  ":param  session_id: Session ID\n"
  ":type   session_id: string\n"
  ":param  data:       Data to be associated with ``session_id``\n"
  ":type   data:       object\n"
  ":rtype: None");
PyObject *smisk_FileSessionStore_write(smisk_FileSessionStore *self, PyObject *args) {
  log_trace("ENTER");
  PyObject *session_id, *data, *fn;
  char *pathname;
  FILE *fp;
  
  if ( PyTuple_GET_SIZE(args) != 2 )
    return PyErr_Format(PyExc_TypeError, "this method takes exactly 2 arguments");
  
  if ( (session_id = PyTuple_GET_ITEM(args, 0)) == NULL )
    return NULL;
  
  if ( (data = PyTuple_GET_ITEM(args, 1)) == NULL )
    return NULL;
  
  if ( (fn = smisk_FileSessionStore_path(self, session_id)) == NULL )
    return NULL;
  
  pathname = PyString_AsString(fn);
  
  if ( (fp = fopen(pathname, "wb")) == NULL)
    return PyErr_SET_FROM_ERRNO;
  
  if (smisk_file_lock(fp, SMISK_FILE_LOCK_NONBLOCK) != 0) {
    // We want to fail silently here, because another process go to the session before we did.
    // Sorry, nothing we can do about it.
    log_debug("smisk_file_lock failed - probably because another process has locked the session");
  }
  else {
    PyMarshal_WriteObjectToFile(data, fp, Py_MARSHAL_VERSION);
    if ((fflush(fp) != 0) || ferror(fp)) {
      PyErr_SetFromErrnoWithFilename(PyExc_IOError, __FILE__);
      log_error("can't write to %s", pathname);
      fclose(fp);
      (void) unlink(pathname);
      return NULL;
    }
    
    if (smisk_file_unlock(fp) != 0) {
      log_debug("Failed to unlock file opened from %s", pathname);
      PyErr_SET_FROM_ERRNO;
      return NULL;
    }
    
    log_debug("Wrote '%s'", pathname);
  }
  
  fclose(fp);
  Py_DECREF(fn);
  Py_RETURN_NONE;
}


PyDoc_STRVAR(smisk_FileSessionStore_refresh_DOC,
  ":param  session_id: Session ID\n"
  ":type   session_id: string\n"
  ":rtype: None");
PyObject *smisk_FileSessionStore_refresh(smisk_FileSessionStore *self, PyObject *session_id) {
  log_trace("ENTER");
  PyObject *fn;
  
  if ( (fn = smisk_FileSessionStore_path(self, session_id)) == NULL )
    return NULL;
  
  if (smisk_file_mtime_set_now(PyString_AsString(fn), -1) != 0) {
    if (errno != ENOENT) {
      PyErr_SET_FROM_ERRNO;
      Py_DECREF(fn);
      return NULL;
    }
#if SMISK_DEBUG
    else {
      log_debug("utimes() failed: '%s' don't exist", PyString_AsString(fn));
    }
#endif
  }
  
  Py_DECREF(fn);
  Py_RETURN_NONE;
}


PyDoc_STRVAR(smisk_FileSessionStore_destroy_DOC,
  ":param  session_id: Session ID\n"
  ":type   session_id: string\n"
  ":rtype: None");
PyObject *smisk_FileSessionStore_destroy(smisk_FileSessionStore *self, PyObject *session_id) {
  log_trace("ENTER");
  PyObject *fn;
  char *pathname;
  
  if ( (fn = smisk_FileSessionStore_path(self, session_id)) == NULL )
    return NULL;
  
  pathname = PyString_AsString(fn);
  
  int failed = smisk_file_exist(pathname) && (_unlink(pathname) != 0);
  Py_DECREF(fn);
  
  if (failed)
    return NULL;
  
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
  
  {"path", (PyCFunction)smisk_FileSessionStore_path, METH_O, smisk_FileSessionStore_path_DOC},
  {NULL, NULL, 0, NULL}
};

// Class members
static struct PyMemberDef smisk_FileSessionStore_members[] = {
  {"file_prefix", T_OBJECT_EX, offsetof(smisk_FileSessionStore, file_prefix), 0, NULL},
  
  {"gc_probability", T_FLOAT, offsetof(smisk_FileSessionStore, gc_probability), 0, NULL},
  
  {NULL, 0, 0, 0, NULL}
};

// Type definition
PyTypeObject smisk_FileSessionStoreType = {
  PyObject_HEAD_INIT(NULL)
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
  0,                           /* tp_new */
  0                            /* tp_free */
};

int smisk_FileSessionStore_register_types(PyObject *module) {
  log_trace("ENTER");
  smisk_FileSessionStoreType.tp_base = &smisk_SessionStoreType;
  if (PyType_Ready(&smisk_FileSessionStoreType) == 0) {
    return PyModule_AddObject(module, "FileSessionStore", (PyObject *)&smisk_FileSessionStoreType);
  }
  return -1;
}
