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
#include "version.h"
#include "module.h"
#include "Application.h"
#include "Request.h"
#include "Response.h"
#include "Stream.h"
#include "NotificationCenter.h"
#include "URL.h"

#include <fastcgi.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <sys/un.h>
#include <arpa/inet.h>

// Set default listensock
int smisk_listensock_fileno = FCGI_LISTENSOCK_FILENO;

// Static objects at module-level
PyObject *smisk_Error, *smisk_IOError;

// Notifications
PyObject *kApplicationWillStartNotification;
PyObject *kApplicationWillExitNotification;
PyObject *kApplicationDidStopNotification;

//#include <fcgi_config.h>
#include <fcgiapp.h>
#include <fastcgi.h>

PyDoc_STRVAR(smisk_bind_DOC,
  "Bind to a specific unix socket or host (and/or port).\n"
  "\n"
  ":param path: The Unix domain socket (named pipe for WinNT), hostname, "
    "hostname and port or just a colon followed by a port number. e.g. "
    "\"/tmp/fastcgi/mysocket\", \"some.host:5000\", \":5000\", \"*:5000\".\n"
  ":param backlog: The listen queue depth used in the listen() call. "
    "Set to negative or zero to let the system decide (recommended).\n"
  ":raises smisk.IOError: On failure.\n"
  ":rtype: None");
PyObject* smisk_bind(PyObject *self, PyObject *args) {
  //int FCGX_OpenSocket(const char *path, int backlog)
  int fd, backlog;
  PyObject* path;
  
  // Set default backlog size (<=0 = let system implementation decide)
  backlog = 0;
  
  // Did we get enough arguments?
  if(!args || PyTuple_GET_SIZE(args) < 1) {
    PyErr_SetString(PyExc_TypeError, "bind takes at least 1 argument");
    return NULL;
  }
  
  // Save reference to first argument and type check it
  path = PyTuple_GET_ITEM(args, 0);
  if(path == NULL || !PyString_Check(path)) {
    PyErr_SetString(PyExc_TypeError, "first argument must be a string");
    return NULL;
  }
  
  // Did we get excplicit backlog size?
  if(PyTuple_GET_SIZE(args) > 1) {
    PyObject* arg1 = PyTuple_GET_ITEM(args, 1);
    if(arg1 != NULL) {
      if(!PyInt_Check(arg1)) {
        PyErr_SetString(PyExc_TypeError, "second argument must be an integer");
        return NULL;
      }
      backlog = (int)PyInt_AS_LONG(arg1);
    }
  }
  
  // Bind/listen
  fd = FCGX_OpenSocket(PyString_AS_STRING(path), backlog);
  if(fd < 0) {
    log_debug("ERROR: FCGX_OpenSocket(\"%s\", %d) returned %d. errno: %d", 
      PyString_AS_STRING(path), backlog, fd, errno);
    return PyErr_SET_FROM_ERRNO_OR_CUSTOM(smisk_IOError, "bind() failed");
  }
	
	// Set the process global fileno
	smisk_listensock_fileno = fd;
  
  Py_RETURN_NONE;
}


PyDoc_STRVAR(smisk_listening_DOC,
  "Find out if this process is a \"remote\" process, bound to a socket "
  "by means of calling bind(). If it is listening, this function returns "
  "the address and port or the UNIX socket path. If not bound, this "
  "function returns None.\n"
  "\n"
  ":raises smisk.IOError: On failure.\n"
  ":rtype: string");
PyObject* smisk_listening(PyObject *self, PyObject *args) {
  PyObject *s = Py_None;
  socklen_t addrlen;
  struct sockaddr *addr;
  
  if(smisk_listensock_fileno == FCGI_LISTENSOCK_FILENO) {
    Py_RETURN_NONE;
  }
  
  addrlen = sizeof(struct sockaddr_in); // Assume INET
  addr = (struct sockaddr *)malloc(addrlen);
  if(getsockname(smisk_listensock_fileno, addr, &addrlen) != 0) {
    return PyErr_SET_FROM_ERRNO_OR_CUSTOM(smisk_IOError, "getsockname() failed");
  }
  
  if(addr->sa_family == AF_INET || addr->sa_family == AF_INET6) {
    char *saddr = "*";
    if(((struct sockaddr_in *)addr)->sin_addr.s_addr != (in_addr_t)0) {
      saddr = (char *)inet_ntoa(((struct sockaddr_in *)addr)->sin_addr);
    }
    s = PyString_FromFormat("%s:%d",
      saddr, 
      htons(((struct sockaddr_in *)addr)->sin_port) );
  }
  else if(addr->sa_family == AF_UNIX) {
    // This may be a bit risky...
    s = PyString_FromString(((struct sockaddr_un *)addr)->sun_path);
  }
  
  if(s == Py_None) {
    Py_INCREF(s);
  }
  return s;
}

/* ------------------------------------------------------------------------- */

static PyMethodDef module_methods[] =
{
  {"bind",     (PyCFunction)smisk_bind,      METH_VARARGS, smisk_bind_DOC},
  {"listening",(PyCFunction)smisk_listening, METH_NOARGS,  smisk_listening_DOC},
  {NULL, NULL, 0, NULL}
};

PyDoc_STRVAR(smisk_module_DOC,
  "Minimal FastCGI-based web application framework.");

PyMODINIT_FUNC initsmisk(void) {
  PyObject* module;
  module = Py_InitModule("smisk", module_methods);
  
  // Register types
  if (!module ||
    (smisk_Application_register_types() != 0) ||
    (smisk_Request_register_types() != 0) ||
    (smisk_Response_register_types() != 0) ||
    (smisk_Stream_register_types() != 0) ||
    (smisk_NotificationCenter_register_types() != 0) ||
    (smisk_URL_register_types() != 0)
    ) {
      goto error;
  }
  
  // Register classes in module
  Py_INCREF(&smisk_ApplicationType);
  PyModule_AddObject(module, "Application", (PyObject *)&smisk_ApplicationType);
  Py_INCREF(&smisk_RequestType);
  PyModule_AddObject(module, "Request", (PyObject *)&smisk_RequestType);
  Py_INCREF(&smisk_ResponseType);
  PyModule_AddObject(module, "Response", (PyObject *)&smisk_ResponseType);
  Py_INCREF(&smisk_StreamType);
  PyModule_AddObject(module, "Stream", (PyObject *)&smisk_StreamType);
  Py_INCREF(&smisk_NotificationCenterType);
  PyModule_AddObject(module, "NotificationCenter", (PyObject *)&smisk_NotificationCenterType);
  Py_INCREF(&smisk_URLType);
  PyModule_AddObject(module, "URL", (PyObject *)&smisk_URLType);
  
  // Setup exceptions
  if (!(smisk_Error = PyErr_NewException("smisk.Error", PyExc_StandardError, NULL))) { goto error; }
  PyModule_AddObject(module, "Error", smisk_Error);
  if (!(smisk_IOError = PyErr_NewException("smisk.IOError", PyExc_IOError, NULL))) { goto error; }
  PyModule_AddObject(module, "IOError", smisk_IOError);
  
  // Setup notifications
#define DEF_NOTI(_name_) \
  if (!(k##_name_ = PyString_FromString(#_name_) )) { goto error; } \
  PyModule_AddObject(module, #_name_, k##_name_);
  
  DEF_NOTI(ApplicationWillStartNotification);
  DEF_NOTI(ApplicationWillExitNotification);
  DEF_NOTI(ApplicationDidStopNotification);
#undef DEF_NOTI
  
  // __version__ and __doc___
  PyModule_AddObject(module, "__version__", PyString_FromString(SMISK_VERSION));
  PyModule_AddObject(module, "__doc__", PyString_FromString(smisk_module_DOC));
  
  
error:
  if (PyErr_Occurred()) {
    PyErr_SetString(PyExc_ImportError, "smisk: init failed");
  }
}

