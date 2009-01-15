/*
Copyright (c) 2007-2009 Rasmus Andersson

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
#include "uid.h"
#include "Application.h"
#include "Request.h"
#include "Response.h"
#include "Stream.h"
#include "URL.h"
#include "SessionStore.h"
#include "FileSessionStore.h"
#include "xml/__init__.h"
#include "bsddb.h"
#include "crash_dump.h"

#include <fastcgi.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <sys/un.h>
#include <arpa/inet.h>
#include <signal.h>
#include <unistd.h>

#include <fcgiapp.h>
#include <fastcgi.h>
#include <fcgios.h>

// Set default listensock
int smisk_listensock_fileno = FCGI_LISTENSOCK_FILENO;

// Objects at module-level
PyObject *smisk_InvalidSessionError;
PyObject *os_module;

// Other static strings (only used in C API)
PyObject *kString_http;
PyObject *kString_https;
PyObject *kString_utf_8;

// Smisk main thread python global interp. lock thread state.
PyThreadState *smisk_py_thstate;


PyObject *smisk_bind(PyObject *self, PyObject *args) {
  log_trace("ENTER");
  int fd, backlog;
  PyObject *path;
  
  // Set default backlog size (<=0 = let system implementation decide)
  backlog = 0;
  
  // Did we get enough arguments?
  if (!args || PyTuple_GET_SIZE(args) < 1) {
    PyErr_SetString(PyExc_TypeError, "bind takes at least 1 argument");
    return NULL;
  }
  
  // Save reference to first argument and type check it
  path = PyTuple_GET_ITEM(args, 0);
  if (path == NULL || !SMISK_STRING_CHECK(path)) {
    PyErr_SetString(PyExc_TypeError, "first argument must be a string");
    return NULL;
  }
  
  if (smisk_listensock_fileno != FCGI_LISTENSOCK_FILENO) {
    return PyErr_Format(PyExc_IOError, "already bound");
  }
  
  // Did we get excplicit backlog size?
  if (PyTuple_GET_SIZE(args) > 1) {
    PyObject *arg1 = PyTuple_GET_ITEM(args, 1);
    if (arg1 != NULL) {
      if (!PyInt_Check(arg1)) {
        PyErr_SetString(PyExc_TypeError, "second argument must be an integer");
        return NULL;
      }
      backlog = (int)PyInt_AS_LONG(arg1);
    }
  }
  
  // Bind/listen
  fd = FCGX_OpenSocket(PyString_AsString(path), backlog);
  if (fd < 0) {
    log_debug("ERROR: FCGX_OpenSocket(\"%s\", %d) returned %d. errno: %d", 
      PyString_AsString(path), backlog, fd, errno);
    return PyErr_SET_FROM_ERRNO;
  }
  
  // Set the process global fileno
  smisk_listensock_fileno = fd;
  
  Py_RETURN_NONE;
}


PyObject *smisk_unbind(PyObject *self) {
  log_trace("ENTER");
  
  if (smisk_listensock_fileno != FCGI_LISTENSOCK_FILENO) {
    if (OS_IpcClose(smisk_listensock_fileno) != 0) {
      log_debug("ERROR: OS_IpcClose(%d) failed. errno: %d",
        smisk_listensock_fileno, errno);
      return PyErr_SET_FROM_ERRNO;
    }
    smisk_listensock_fileno = FCGI_LISTENSOCK_FILENO;
  }
  
  Py_RETURN_NONE;
}


PyObject *smisk_listening(PyObject *self, PyObject *args) {
  log_trace("ENTER");
  PyObject *s = Py_None;
  socklen_t addrlen;
  struct sockaddr *addr;
  
  if (smisk_listensock_fileno == FCGI_LISTENSOCK_FILENO)
    Py_RETURN_NONE;
  
  addrlen = sizeof(struct sockaddr_in); // Assume INET
  addr = (struct sockaddr *)malloc(addrlen);
  if (getsockname(smisk_listensock_fileno, addr, &addrlen) != 0)
    return PyErr_SET_FROM_ERRNO;
  
  if (addr->sa_family == AF_INET || addr->sa_family == AF_INET6) {
    char *saddr = "*";
    if (((struct sockaddr_in *)addr)->sin_addr.s_addr != (in_addr_t)0) {
      saddr = (char *)inet_ntoa(((struct sockaddr_in *)addr)->sin_addr);
    }
    s = PyString_FromFormat("%s:%d",
      saddr, 
      htons(((struct sockaddr_in *)addr)->sin_port) );
  }
  else if (addr->sa_family == AF_UNIX) {
    // XXX: This may be a bit risky...
    s = PyString_FromString(((struct sockaddr_un *)addr)->sun_path);
  }
  
  if (s == Py_None)
    Py_INCREF(s);
  
  return s;
}


PyObject *smisk_uid(PyObject *self, PyObject *args) {
  log_trace("ENTER");
  PyObject *node = NULL;
  int nbits = 5;
  smisk_uid_t uid;
  
  // nbits
  if (PyTuple_GET_SIZE(args) > 0) {
    PyObject *arg = PyTuple_GET_ITEM(args, 0);
    if (arg != NULL && arg != Py_None) {
      if (!PyInt_Check(arg)) {
        PyErr_SetString(PyExc_TypeError, "first argument must be an integer");
        return NULL;
      }
      nbits = (int)PyInt_AS_LONG(arg);
    }
  }
  
  // node
  if (PyTuple_GET_SIZE(args) > 1) {
    node = PyTuple_GET_ITEM(args, 1);
    if (node == Py_None) {
      node = NULL;
    }
    else if (node == NULL || !SMISK_STRING_CHECK(node)) {
      PyErr_SetString(PyExc_TypeError, "second argument must be a string");
      return NULL;
    }
  }
  
  if ((node ? smisk_uid_create(&uid, PyString_AsString(node), PyString_Size(node))
            : smisk_uid_create(&uid, NULL, 0)) == -1) {
    PyErr_SetString(PyExc_SystemError, "smisk_uid_create() failed");
    return NULL;
  }
  
  if ( (nbits == 0) || (nbits == -1) )
    return PyString_FromStringAndSize((const char *)uid.digest, 20);
  else
    return smisk_uid_format(&uid, nbits);
}


PyObject *smisk_pack(PyObject *self, PyObject *args) {
  log_trace("ENTER");
  PyObject *data = NULL;
  int nbits = 5;
  
  // data
  if (PyTuple_GET_SIZE(args) > 0) {
    data = PyTuple_GET_ITEM(args, 0);
    if (data == NULL || !SMISK_STRING_CHECK(data)) {
      PyErr_SetString(PyExc_TypeError, "first argument must be a string");
      return NULL;
    }
  }
  
  // nbits
  if (PyTuple_GET_SIZE(args) > 1) {
    PyObject *arg = PyTuple_GET_ITEM(args, 1);
    if (arg != NULL) {
      if (!PyInt_Check(arg)) {
        PyErr_SetString(PyExc_TypeError, "second argument must be an integer");
        return NULL;
      }
      nbits = (int)PyInt_AS_LONG(arg);
    }
  }
  
  return smisk_util_pack((const byte *)PyString_AsString(data), PyString_Size(data), nbits);
}


static PyObject *_object_hash(PyObject *self, PyObject *obj) {
  log_trace("ENTER");
  long h = smisk_object_hash(obj);
  if (h == -1)
    return NULL;
  // 'confirm_token']='v8u6uog961lvq646aeda55i20isn2pl7'
  return PyLong_FromLong(h);
}


/* ------------------------------------------------------------------------- */

static PyMethodDef module_methods[] = {
  {"bind",        (PyCFunction)smisk_bind,      METH_VARARGS, NULL},
  {"unbind",      (PyCFunction)smisk_unbind,    METH_NOARGS,  NULL},
  {"listening",   (PyCFunction)smisk_listening, METH_NOARGS,  NULL},
  {"uid",         (PyCFunction)smisk_uid,       METH_VARARGS, NULL},
  {"pack",        (PyCFunction)smisk_pack,      METH_VARARGS, NULL},
  {"object_hash", (PyCFunction)_object_hash,    METH_O,       NULL},
  {NULL, NULL, 0, NULL}
};


PyMODINIT_FUNC initcore(void) {
  log_trace("ENTER");
  int rc;
  
  // Initialize libfcgi
  if(FCGX_Init() != 0) {
		PyErr_SetString(PyExc_ImportError, "smisk.core: FCGX_Init() failed");
		return;
	}
  
  // Create module
  if ((smisk_core_module = Py_InitModule("smisk.core", module_methods)) == NULL)
    return;
  
  // Initialize crash dumper
  smisk_crash_dump_init();
  
  // import os
  os_module = PyImport_ImportModule("os");
  if (os_module == NULL)
    return;
  
  // Constants: Other static strings (only used in C API)
  kString_http = PyString_InternFromString("http");
  kString_https = PyString_InternFromString("https");
  kString_utf_8 = PyString_InternFromString("utf-8");
  
  // Constants: Special variables
  if (PyModule_AddStringConstant(smisk_core_module, "__build__", SMISK_BUILD_ID) != 0)
    return;
  
  // Register types
  #define R(name, okstmt) \
    if (smisk_ ## name(smisk_core_module) okstmt) { \
      log_error("sub-component initializer '" #name "' failed"); \
      return; \
    }
  R(Application_register_types, != 0);
  R(Application_register_types, != 0);
  R(Application_register_types, != 0);
  R(Request_register_types, != 0);
  R(Response_register_types, != 0);
  R(Stream_register_types, != 0);
  R(URL_register_types, != 0);
  R(SessionStore_register_types, != 0);
  R(FileSessionStore_register_types, != 0);
  R(xml_register, == NULL);
  R(bsddb_register, == NULL);
  #undef R
  
  // Exceptions
  if (!(smisk_InvalidSessionError = PyErr_NewException("smisk.core.InvalidSessionError", PyExc_ValueError, NULL))
    ||
    (PyModule_AddObject(smisk_core_module, "InvalidSessionError", smisk_InvalidSessionError) == -1)
    )
  {
    return;
  }
  
  // Setup ObjectProxies for app, request and response
  PyObject *smisk_util_objectproxy = PyImport_ImportModule("smisk.util.objectproxy");
  if (smisk_util_objectproxy == NULL)
    return;
  PyObject *ObjectProxy = PyObject_GetAttrString(smisk_util_objectproxy, "ObjectProxy");
  Py_DECREF(smisk_util_objectproxy);
  if (ObjectProxy == NULL)
    return;
  rc = PyModule_AddObject(smisk_core_module, "app", PyObject_CallMethod(ObjectProxy, "__new__", "O", ObjectProxy));
  if (rc == 0)
    rc = PyModule_AddObject(smisk_core_module, "request", PyObject_CallMethod(ObjectProxy, "__new__", "O", ObjectProxy));
  if (rc == 0)
    rc = PyModule_AddObject(smisk_core_module, "response", PyObject_CallMethod(ObjectProxy, "__new__", "O", ObjectProxy));
  Py_DECREF(ObjectProxy);
  if (rc != 0) {
    // Error occured in one of the calls to PyModule_AddObject
    return;
  }
  
  /* Original comment from _bsddb.c in the Python core. This is also still
   * needed nowadays for Python 2.3/2.4.
   * 
   * PyEval_InitThreads is called here due to a quirk in python 1.5
   * - 2.2.1 (at least) according to Russell Williamson <merel@wt.net>:
   * The global interpreter lock is not initialized until the first
   * thread is created using thread.start_new_thread() or fork() is
   * called.  that would cause the ALLOW_THREADS here to segfault due
   * to a null pointer reference if no threads or child processes
   * have been created.  This works around that and is a no-op if
   * threads have already been initialized.
   *  (see pybsddb-users mailing list post on 2002-08-07)
   */
  PyEval_InitThreads();
}

