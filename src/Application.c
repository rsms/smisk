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
#include "Application.h"
#include "NotificationCenter.h"
#include "FileSessionStore.h"

#include <fcgiapp.h>
#include <fastcgi.h>

#include <structmember.h>
#include <signal.h>
#include <limits.h> // for PATH_MAX
#include <libgen.h>

#pragma mark Public C

smisk_Application *smisk_current_app = NULL;


#pragma mark -
#pragma mark Internal

static int _setup_transaction_context(smisk_Application *self) {
  log_debug("ENTER _setup_transaction_context");
  PyObject *request, *response;
  
  // Request
  if((request = smisk_Request_new(self->request_class, NULL, NULL)) == NULL) {
    return -1;
  }
  REPLACE_OBJ(self->request, request, smisk_Request);
  assert_refcount(self->request, > 0);
  
  
  // Response
  if((response = smisk_Response_new(self->response_class, NULL, NULL)) == NULL) {
    return -1;
  }
  REPLACE_OBJ(self->response, response, smisk_Response);
  assert_refcount(self->response, > 0);
  
  
  return 0;
}


// signal handlers wrapping run method

int smisk_Application_trapped_signal = 0;

static void smisk_Application_sighandler_close_fcgi(int sig) {
  log_debug("Caught signal %d", sig);
  smisk_Application_trapped_signal = sig;
  FCGX_ShutdownPending();
}


#pragma mark -
#pragma mark Initialization & deallocation

PyObject * smisk_Application_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {
  log_debug("ENTER smisk_Application_new");
  smisk_Application *self;
  
  self = (smisk_Application *)type->tp_alloc(type, 0);
  if (self != NULL) {
    // Set default classes
    self->request_class = (PyTypeObject*)&smisk_RequestType;
    self->response_class = (PyTypeObject*)&smisk_ResponseType;
    self->session_store_class = (PyTypeObject*)&smisk_FileSessionStoreType;
  
    // Set transaction context to None - run() will set up these.
    self->request = (smisk_Request *)Py_None; Py_INCREF(Py_None);
    self->response = (smisk_Response *)Py_None; Py_INCREF(Py_None);
    
    // Nullify lazy objects
    self->session_store = NULL;
  
    // Default values
    self->session_id_size = 20;
    self->session_ttl = 900;
    self->session_name = PyString_FromString("SID");
    self->include_exc_info_with_errors = Py_True; Py_INCREF(Py_True);
    
    // Application.current = self
    REPLACE_OBJ(smisk_current_app, self, smisk_Application);
  }
  
  return (PyObject *)self;
}


int smisk_Application_init(smisk_Application *self, PyObject* args, PyObject* kwargs) {
  return 0;
}


void smisk_Application_dealloc(smisk_Application *self) {
  log_debug("ENTER smisk_Application_dealloc");
  if(smisk_current_app == self) {
    REPLACE_OBJ(smisk_current_app, NULL, smisk_Application);
  }
  Py_DECREF(self->request);
  Py_DECREF(self->response);
  Py_DECREF(self->session_store);
  Py_DECREF(self->session_name);
  Py_DECREF(self->include_exc_info_with_errors);
  
  self->ob_type->tp_free((PyObject*)self);
}


#pragma mark -
#pragma mark Methods


PyDoc_STRVAR(smisk_Application_run_DOC,
  "Run application.\n"
  "\n"
  ":rtype: None");
PyObject* smisk_Application_run(smisk_Application *self, PyObject* args) {
  log_debug("ENTER smisk_Application_run");
  
  PyOS_sighandler_t orig_int_handler, orig_hup_handler, orig_term_handler;
  PyObject *ret = Py_None;
  
  // Set program name to argv[0]
  PyObject* argv = PySys_GetObject("argv");
  if(PyList_GET_SIZE(argv)) {
    Py_SetProgramName(basename(PyString_AsString(PyList_GetItem(argv, 0))));
  }
  
  // Initialize libfcgi
  FCGX_Request request;
  int rc = FCGX_Init();
  if (rc) {
    return PyErr_SET_FROM_ERRNO_OR_CUSTOM(smisk_IOError, "Failed to initialize libfcgi");
  }
  FCGX_InitRequest(&request, smisk_listensock_fileno, FCGI_FAIL_ACCEPT_ON_INTR);
  
  // Register signal handlers
  orig_int_handler = PyOS_setsig(SIGINT, smisk_Application_sighandler_close_fcgi);
  orig_hup_handler = PyOS_setsig(SIGHUP, smisk_Application_sighandler_close_fcgi);
  orig_term_handler = PyOS_setsig(SIGTERM, smisk_Application_sighandler_close_fcgi);
  
  // CGI test
  if(FCGX_IsCGI() && (smisk_listensock_fileno == FCGI_LISTENSOCK_FILENO)) {
    return PyErr_Format(smisk_Error, "Application must be run in a FastCGI environment");
  }
  
  // Create transaction context
  if(_setup_transaction_context(self) != 0) {
    return NULL;
  }
  
  if(!POST_NOTIFICATION1(kApplicationWillStartNotification, self)) {
    return NULL;
  }
  
  // Enter accept loop
  while (FCGX_Accept_r(&request) != -1) {
    if(smisk_Application_trapped_signal) {
      break;
    }
    log_debug("%s %s from %s:%s",
      FCGX_GetParam("REQUEST_METHOD", request.envp),
      FCGX_GetParam("REQUEST_URI", request.envp),
      FCGX_GetParam("REMOTE_ADDR", request.envp),
      FCGX_GetParam("REMOTE_PORT", request.envp) );
    
    // Set streams (TODO: check if this really is needed)
    self->request->input->stream = request.in;
    self->response->out->stream  = request.out;
    self->request->err->stream   = request.err;
    self->request->envp          = request.envp;
    
    
    // Service request
    if(PyObject_CallMethod((PyObject *)self, "service", NULL) != NULL) {
      // Finish request
      smisk_Response_finish(self->response);
    }
    IFDEBUG(else if(!smisk_Application_trapped_signal) {
      log_debug("<Application@%p>.service() failed", self);
    })
    
    // Exception raised?
    if(PyErr_Occurred()) {
      if(smisk_Application_trapped_signal) {
        PyErr_Print();
        break;
      }
      else {
        PyObject *type, *value, *tb;
        PyErr_Fetch(&type, &value, &tb);
        PyErr_Clear();
        log_debug("PyError: %p, %p, %p", type, value, tb);
        PyObject *err_ret = PyObject_CallMethod((PyObject *)self, "error", "OOO", type, value, tb);
        Py_DECREF(type);
        Py_DECREF(value);
        Py_DECREF(tb);
        if(err_ret != NULL) {
          Py_DECREF(err_ret);
        }
        else {
          // Exit run loop if sending the error failed
          log_error("Failed to send error message because of another error");
          PyErr_Print();
          raise(SIGINT);
          break;
        }
      }
    }
    
    // Reset request & response
    if( (smisk_Request_reset(self->request) != 0) || (smisk_Response_reset(self->response) != 0) ) {
      log_debug("Reqeust.reset() or Response.reset() failed");
      PyErr_Print();
      raise(SIGINT);
    }
  }
  
  //FCGX_Finish();
  FCGX_Finish_r(&request);
  
  // Notify observers
  ret = POST_NOTIFICATION1(kApplicationDidStopNotification, self);
  
  // reset signal handlers
  PyOS_setsig(SIGINT, orig_int_handler);
  PyOS_setsig(SIGHUP, orig_hup_handler);
  PyOS_setsig(SIGTERM, orig_term_handler);
  
  // Notify observers
  if(ret != NULL) {
    ret = POST_NOTIFICATION1(kApplicationWillExitNotification, self);
  }
  
  // Now, raise the signal again if that was the reason for exiting the run loop
  if(smisk_Application_trapped_signal) {
    log_debug("raising signal %d again", smisk_Application_trapped_signal);
    raise(smisk_Application_trapped_signal);
    smisk_Application_trapped_signal = 0;
  }
  
  log_debug("EXIT smisk_Application_run");
  if(ret == Py_None) {
    Py_INCREF(ret);
  }
  return ret;
}


PyDoc_STRVAR(smisk_Application_service_DOC,
  "Service a request.\n"
  "\n"
  ":rtype: None");
PyObject* smisk_Application_service(smisk_Application *self, PyObject* args) {
  log_debug("ENTER smisk_Application_service");
  
  FCGX_FPrintF(self->response->out->stream,
     "Content-type: text/html\r\n"
     "\r\n"
     "<html><head><title>Smisk instance #%d</title></head><body>"
     "<h1>Smisk instance #%d</h1>\n"
     "No services available"
     "</body></html>\n", getpid(), getpid());
  
  Py_RETURN_NONE;
}


PyDoc_STRVAR(smisk_Application_error_DOC,
  "Service a error message.\n"
  "\n"
  ":param typ: Exception type\n"
  ":type  typ: type\n"
  ":param val: Exception value\n"
  ":type  val: Exception\n"
  ":param tb:  Traceback\n"
  ":type  tb:  object\n"
  ":rtype: None");
PyObject* smisk_Application_error(smisk_Application *self, PyObject* args) {
  log_debug("ENTER smisk_Application_error");
  
  int rc;
  PyObject *msg, *exc_str, *type, *value, *tb;
  
  if(!PyArg_UnpackTuple(args, "error", 3, 3, &type, &value, &tb)) {
    return NULL;
  }
  
  // Format exception into string
  if( (exc_str = format_exc(type, value, tb)) == NULL ) {
    return NULL;
  }
  
  ENSURE_BY_GETTER(self->request->env, smisk_Request_get_env(self->request),
    return NULL;
  );
  
  // Format error message
  msg = PyString_FromFormat("<h1>Internal Server Error</h1>\n"
    "<pre>%s</pre>\n"
    "<hr/><address>%s at %s port %s</address>\n",
    ((self->include_exc_info_with_errors == Py_True) ? PyString_AS_STRING(exc_str) : "Exception info has been logged."),
    PyString_AS_STRING(PyDict_GetItemString(self->request->env, "SERVER_SOFTWARE")),
    FCGX_GetParam("SERVER_NAME", self->request->envp),
    FCGX_GetParam("SERVER_PORT", self->request->envp));
  
  // Log exception
  if(FCGX_PutStr(PyString_AS_STRING(exc_str), PyString_GET_SIZE(exc_str), self->request->err->stream) == -1) {
    log_error("Error in %s.error(): %s", PyString_AS_STRING(PyObject_Str((PyObject *)self)), PyString_AS_STRING(exc_str));
    return PyErr_SET_FROM_ERRNO_OR_CUSTOM(smisk_IOError, "Failed to write on err stream");
  }
  
  Py_DECREF(exc_str);
  
  if(!self->response->has_begun) {
    // Include headers if response has not yet been sent
    static char *header = "<html><head><title>Internal Server Error</title></head><body>";
    static char *footer = "</body></html>";
    rc = FCGX_FPrintF(self->response->out->stream,
       "Content-Type: text/html\r\n"
      "Status: 500 Internal Server Error\r\n"
      "Content-Length: %ld\r\n"
       "\r\n"
       "%s%s%s\r\n",
      strlen(header)+PyString_GET_SIZE(msg)+strlen(footer)+2,
      header,
      PyString_AS_STRING(msg),
      footer);
  }
  else {
    rc = FCGX_PutStr( PyString_AS_STRING(msg),
                      PyString_GET_SIZE(msg),
                      self->response->out->stream);
  }
  
  Py_DECREF(msg);
  
  if(rc == -1) {
    return PyErr_SET_FROM_ERRNO_OR_CUSTOM(smisk_IOError, "Failed to write on stream");
  }
  
  Py_RETURN_NONE;
}


PyDoc_STRVAR(smisk_Application_exit_DOC,
  "Exit application.\n"
  "\n"
  ":rtype: None");
PyObject *smisk_Application_exit(smisk_Application *self) {
  raise(2); // SIG_INT
  Py_RETURN_NONE;
}


PyDoc_STRVAR(smisk_Application_current_DOC,
  "Current application instance, if any.\n"
  "\n"
  ":rtype: Application");
PyObject *smisk_Application_current(smisk_Application *self) {
  Py_XINCREF(smisk_current_app);
  return (PyObject *)smisk_current_app;
}


PyObject* smisk_Application_get_session_store(smisk_Application* self) {
  log_debug("ENTER smisk_Application_get_session_store");
  if(self->session_store == NULL) {
    DUMP_REPR(self->session_store_class);
    if((self->session_store = PyObject_Call((PyObject*)self->session_store_class, NULL, NULL)) == NULL) {
      return NULL;
    }
    log_debug("self->session_store=%p", self->session_store);
  }
  
  Py_INCREF(self->session_store); // callers reference
  return self->session_store;
}


static int smisk_Application_set_session_store(smisk_Application* self, PyObject *session_store) {
  log_debug("ENTER smisk_Application_set_session_store  session_store=%p", session_store);
  REPLACE_OBJ(self->session_store, session_store, PyObject);
  return self->session_store ? 0 : -1;
}


/********** type configuration **********/

PyDoc_STRVAR(smisk_Application_DOC,
  "An application.\n"
  "\n"
  "Notifications whis is emitted by an Application:\n"
  " * `ApplicationWillStartNotification` - Emitted just before the application starts accept()'ing.\n"
  " * `ApplicationDidStopNotification` - The application stopped accepting connections.\n"
  " * `ApplicationWillExitNotification` - The application is about to exit from a signal or by ending it's run loop.\n");

// Methods
static PyMethodDef smisk_Application_methods[] = {
  {"run",     (PyCFunction)smisk_Application_run,     METH_VARARGS, smisk_Application_run_DOC},
  {"service", (PyCFunction)smisk_Application_service, METH_VARARGS, smisk_Application_service_DOC},
  {"error",   (PyCFunction)smisk_Application_error,   METH_VARARGS, smisk_Application_error_DOC},
  {"exit",    (PyCFunction)smisk_Application_exit,    METH_NOARGS,  smisk_Application_exit_DOC},
  {"current", (PyCFunction)smisk_Application_current, METH_STATIC|METH_NOARGS, smisk_Application_current_DOC},
  {NULL}
};

// Properties
static PyGetSetDef smisk_Application_getset[] = {
  {"session_store",
    (getter)smisk_Application_get_session_store,
    (setter)smisk_Application_set_session_store,
    ":type: `smisk.session.Store`", NULL},
  
  {NULL}
};

// Members
static struct PyMemberDef smisk_Application_members[] = {
  {"request_class",  T_OBJECT_EX, offsetof(smisk_Application, request_class), 0,
    ":type: Type\n\n"
    "Must be set before calling `run()`"},
  
  {"response_class", T_OBJECT_EX, offsetof(smisk_Application, response_class), 0,
    ":type: Type\n\n"
    "Must be set before calling `run()`"},
  
  {"session_store_class",  T_OBJECT_EX, offsetof(smisk_Application, session_store_class), 0,
    ":type: Type\n\n"
    "Must be set before first access to `session_store`"},
  
  {"request",  T_OBJECT_EX, offsetof(smisk_Application, request),  RO,
    ":type: `Request`"},
  
  {"response", T_OBJECT_EX, offsetof(smisk_Application, response), RO,
    ":type: `Response`"},
  
  {"include_exc_info_with_errors", T_OBJECT_EX, offsetof(smisk_Application, include_exc_info_with_errors), 0,
    ":type: bool\n\n"
    "Defaults to True."},
  
  {"session_id_size", T_INT, offsetof(smisk_Application, session_id_size), 0,
    ":type: int\n\n"
    "How big and complex generated session IDs should be, expressed in bytes. Defaults to 20."},
  
  {"session_name", T_OBJECT_EX, offsetof(smisk_Application, session_name), 0,
    ":type: string\n\n"
    "Name used to identify the session id cookie. Defaults to \"SID\""},
  
  {"session_ttl", T_INT, offsetof(smisk_Application, session_ttl), 0,
    ":type: int\n\n"
    "For how long a session should be valid, expressed in seconds. Defaults to 900."},
  
  {NULL}
};

// Class
PyTypeObject smisk_ApplicationType = {
  PyObject_HEAD_INIT(&PyType_Type)
  0,             /*ob_size*/
  "smisk.core.Application",       /*tp_name*/
  sizeof(smisk_Application),     /*tp_basicsize*/
  0,             /*tp_itemsize*/
  (destructor)smisk_Application_dealloc,    /* tp_dealloc */
  0,             /*tp_print*/
  0,             /*tp_getattr*/
  0,             /*tp_setattr*/
  0,             /*tp_compare*/
  0,             /*tp_repr*/
  0,             /*tp_as_number*/
  0,             /*tp_as_sequence*/
  0,             /*tp_as_mapping*/
  0,             /*tp_hash */
  0,             /*tp_call*/
  0,             /*tp_str*/
  0,             /*tp_getattro*/
  0,             /*tp_setattro*/
  0,             /*tp_as_buffer*/
  Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE, /*tp_flags*/
  smisk_Application_DOC,      /*tp_doc*/
  (traverseproc)0,       /* tp_traverse */
  0,             /* tp_clear */
  0,             /* tp_richcompare */
  0,             /* tp_weaklistoffset */
  0,             /* tp_iter */
  0,             /* tp_iternext */
  smisk_Application_methods,  /* tp_methods */
  smisk_Application_members,  /* tp_members */
  smisk_Application_getset,   /* tp_getset */
  0,               /* tp_base */
  0,               /* tp_dict */
  0,               /* tp_descr_get */
  0,               /* tp_descr_set */
  0,               /* tp_dictoffset */
  (initproc)smisk_Application_init, /* tp_init */
  0,               /* tp_alloc */
  smisk_Application_new,       /* tp_new */
  0              /* tp_free */
};

int smisk_Application_register_types(PyObject *module) {
  if(PyType_Ready(&smisk_ApplicationType) == 0) {
    return PyModule_AddObject(module, "Application", (PyObject *)&smisk_ApplicationType);
  }
  return -1;
}
