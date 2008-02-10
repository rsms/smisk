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
#include "version.h"
#include "utils.h"
#include "Application.h"
#include "NotificationCenter.h"

#include <fcgiapp.h>
#include <fastcgi.h>

#include <structmember.h>
#include <signal.h>

//#include <unistd.h>
#include <libgen.h>

/**************** signal handlers wrapping run method *******************/

int smisk_Application_trapped_signal = 0;

void smisk_Application_sighandler_close_fcgi(int sig) {
  log_debug("Caught signal %d", sig);
  smisk_Application_trapped_signal = sig;
  FCGX_ShutdownPending();
}


/************************* instance methods *****************************/

int smisk_Application_init(smisk_Application* self, PyObject* args, PyObject* kwargs) {
  log_debug("ENTER smisk_Application_init");
  
  // Construct a new Request item
  if(self->requestClass == NULL) {
      self->requestClass = (PyTypeObject*)&smisk_RequestType;
   }
  self->request = (smisk_Request*)PyObject_Call((PyObject*)self->requestClass, NULL, NULL);
  if (self->request == NULL) {
    log_debug("self->request == NULL");
    Py_DECREF(self);
    return -1;
  }
  
  // Construct a new Response item
  if(self->responseClass == NULL) {
      self->responseClass = (PyTypeObject*)&smisk_ResponseType;
   }
  self->response = (smisk_Response*)PyObject_Call((PyObject*)self->responseClass, NULL, NULL);
  if (self->response == NULL) {
    log_debug("self->response == NULL");
    Py_DECREF(self);
    return -1;
  }
  self->response->app = (PyObject *)self;
  
  // TODO: Make get/settable
  self->includeExceptionInfoInErrors = 1;
  
  return 0;
}


void smisk_Application_dealloc(smisk_Application* self) {
  log_debug("ENTER smisk_Application_dealloc");
  Py_DECREF(self->request);
}


PyDoc_STRVAR(smisk_Application_run_DOC,
  "Run application.\n"
  "\n"
  ":rtype: None");
PyObject* smisk_Application_run(smisk_Application* self, PyObject* args) {
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
  
  if(!POST_NOTIFICATION1(kApplicationWillStartNotification, self)) {
    return NULL;
  }
  
  // Enter accept loop
  while (FCGX_Accept_r(&request) != -1) {
     if(smisk_Application_trapped_signal) {
         break;
     }
     
    // Set streams (TODO: check if this really is needed)
    self->request->input->stream = request.in;
    self->response->out->stream  = request.out;
    self->request->err->stream   = request.err;
    self->request->envp          = request.envp;
    
    // Reset request & response
    if((smisk_Request_reset(self->request) == 0) && (smisk_Response_reset(self->response) == 0)) {
      // Service request
      if(PyObject_CallMethod((PyObject *)self, "service", NULL) != NULL) {
        // Finish request
        smisk_Response_finish(self->response);
      }
      else if(!smisk_Application_trapped_signal) {
         log_debug("PyObject_CallMethod(self, service) FAILED");
      }
    }
    else {
       log_debug("Failed to reset request and/or response");
    }
    
    // Exception raised?
    if(PyErr_Occurred()) {
       if(smisk_Application_trapped_signal) {
          PyErr_Print();
            break;
       }
       else {
         // Call on self.error
         if(PyObject_CallMethod((PyObject *)self, "error", NULL) == NULL) {
           // Exit run loop if sending the error failed
           log_error("Failed to send error message because of another error:");
           PyErr_Print();
           raise(SIGINT);
           break;
         }
       }
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
PyObject* smisk_Application_service(smisk_Application* self, PyObject* args) {
  log_debug("ENTER smisk_Application_service");
  
  FCGX_FPrintF(self->response->out->stream,
     "Content-type: text/html\r\n"
     "\r\n"
     "<title>FastCGI echo (fcgiapp version)</title>"
     "<h1>FastCGI echo (fcgiapp version)</h1>\n"
     "Process ID: %d<p>\n", getpid());
  
  Py_RETURN_NONE;
}


PyDoc_STRVAR(smisk_Application_error_DOC,
  "Service a error message.\n"
  "\n"
  ":rtype: None");
PyObject* smisk_Application_error(smisk_Application* self, PyObject* args) {
  log_debug("ENTER smisk_Application_error");
  
  int rc;
  PyObject *msg, *exc_str;
  
  // Format exception into string
  if( (exc_str = format_exc()) == NULL ) {
    return NULL;
  }
  
  // Format error message
  msg = PyString_FromFormat("<h1>Internal Server Error</h1>\n"
    "<pre>%s</pre>\n"
    "<hr/><address>%s smisk/%s at %s port %s</address>\n",
    (self->includeExceptionInfoInErrors ? PyString_AS_STRING(exc_str) : "Exception info has been logged."),
    FCGX_GetParam("SERVER_SOFTWARE", self->request->envp),
    SMISK_VERSION,
    FCGX_GetParam("SERVER_ADDR", self->request->envp),
    FCGX_GetParam("SERVER_PORT", self->request->envp));
  
  // Log exception
  if(FCGX_PutStr(PyString_AS_STRING(exc_str), PyString_GET_SIZE(exc_str), self->request->err->stream) == -1) {
    log_error("Error in %s.service(): %s", PyString_AS_STRING(PyObject_Str((PyObject *)self)), PyString_AS_STRING(exc_str));
    return PyErr_SET_FROM_ERRNO_OR_CUSTOM(smisk_IOError, "Failed to write on err stream");
  }
  
  Py_DECREF(exc_str);
  
  if(!self->response->has_begun) {
    // Include headers if response has not yet been sent
    rc = FCGX_FPrintF(self->response->out->stream,
       "Content-Type: text/html\r\n"
      "Status: 500 Internal Server Error\r\n"
      "Content-Length: %ld\r\n"
       "\r\n"
       "<html><head><title>Internal Server Error</title></head><body>"
       "%s"
       "</body></html>",
      PyString_GET_SIZE(msg),
      PyString_AS_STRING(msg));
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
PyObject* smisk_Application_exit(smisk_Application* self) {
  raise(2); // SIG_INT
  Py_RETURN_NONE;
}


/********** type configuration **********/

PyDoc_STRVAR(smisk_Application_DOC,
  "An application.\n"
  "\n"
  "Notifications whis is emitted by an Application:\n"
  " * ApplicationServiceError - When an exception happens in service(). Emitted before calling on error().\n"
  " * ApplicationWillStart - Emitted just before the application starts accept()'ing.\n"
  " * ApplicationWillExit - The application is about to exit from a signal or by ending it's run loop.\n"
  " * ApplicationStoppedAccepting - The application stopped accepting connections.\n"
  "\n"
  ":ivar request:  Request object (read-only)\n"
  ":type request:  smisk.Request\n"
  ":ivar response: Response object (read-only)\n"
  ":type response: smisk.Response\n");

// TODO: Application.requestClass and Application.responseClass

// Methods
static PyMethodDef smisk_Application_methods[] =
{
  {"run",     (PyCFunction)smisk_Application_run,     METH_VARARGS, smisk_Application_run_DOC},
  {"service", (PyCFunction)smisk_Application_service, METH_VARARGS, smisk_Application_service_DOC},
  {"error",   (PyCFunction)smisk_Application_error,   METH_VARARGS, smisk_Application_error_DOC},
  {"exit",     (PyCFunction)smisk_Application_exit,    METH_NOARGS,  smisk_Application_exit_DOC},
  {NULL}
};

// Properties (Members)
static struct PyMemberDef smisk_Application_members[] =
{
  {"requestClass",  T_OBJECT_EX, offsetof(smisk_Application, requestClass),  0, NULL},
  {"responseClass", T_OBJECT_EX, offsetof(smisk_Application, responseClass), 0, NULL},
  {"request",  T_OBJECT_EX, offsetof(smisk_Application, request),  RO, NULL},
  {"response", T_OBJECT_EX, offsetof(smisk_Application, response), RO, NULL},
  {NULL}
};

// Class
PyTypeObject smisk_ApplicationType = {
  PyObject_HEAD_INIT(&PyType_Type)
  0,             /*ob_size*/
  "smisk.Application",       /*tp_name*/
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
  0,               /* tp_getset */
  0,               /* tp_base */
  0,               /* tp_dict */
  0,               /* tp_descr_get */
  0,               /* tp_descr_set */
  0,               /* tp_dictoffset */
  (initproc)smisk_Application_init, /* tp_init */
  0,               /* tp_alloc */
  PyType_GenericNew,       /* tp_new */
  0              /* tp_free */
};

extern int smisk_Application_register_types(void) {
  return PyType_Ready(&smisk_ApplicationType);
}
