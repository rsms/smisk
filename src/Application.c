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
#include "utils.h"
#include "Application.h"
#include "FileSessionStore.h"

#include <fcgiapp.h>
#include <fastcgi.h>

#include <signal.h>
#include <limits.h> // for PATH_MAX
#include <libgen.h>

#include <sys/wait.h>


#pragma mark Public C


smisk_Application *smisk_Application_current = NULL;

// Set error if smisk_Application_current is NULL.
int smisk_require_app (void) {
  log_trace("ENTER");
  if ( (smisk_Application_current == NULL) || (smisk_Application_current == (smisk_Application *)Py_None) ) {
    PyErr_SetString(PyExc_EnvironmentError, "Application not initialized");
    return -1;
  }
  return 0;
}

// Returns 0 on success, -1 on failure.
int smisk_Application_set_current (PyObject *app) {
  PyObject *old = SMISK_PyObject_GET(&smisk_ApplicationType, "current");
  int st = SMISK_PyObject_SET(&smisk_ApplicationType, "current", app);
  if (st == -1) {
    // Revert to None on error
    Py_INCREF(Py_None);
    smisk_Application_current = (smisk_Application *)Py_None;
    if (SMISK_PyObject_SET(&smisk_ApplicationType, "current", Py_None) == -1) {
      Py_DECREF(Py_None);
    }
  }
  else {
    // Aquire a new reference
    Py_INCREF(app);
    smisk_Application_current = (smisk_Application *)app;
  }
  // Release any reference to old object
  Py_XDECREF(old);
  return st;
}


#pragma mark -
#pragma mark Internal


static int _setup_transaction_context(smisk_Application *self) {
  log_trace("ENTER");
  PyObject *request, *response, *objproxy, *rc;
  
  // Request
  if ((request = smisk_Request_new(self->request_class, NULL, NULL)) == NULL)
    return -1;
  
  REPLACE_OBJ(self->request, request, smisk_Request);
  assert_refcount(self->request, > 0);
  
  // smisk.core.request = self.request
  objproxy = PyObject_GetAttrString(smisk_core_module, "request");
  rc = PyObject_CallMethod(objproxy, "_set_object", "O", (PyObject *)self->request);
  Py_DECREF(objproxy);
  if (rc == NULL)
    return -1;
  Py_DECREF(rc);
  
  
  // Response
  if ((response = smisk_Response_new(self->response_class, NULL, NULL)) == NULL)
    return -1;
  
  REPLACE_OBJ(self->response, response, smisk_Response);
  assert_refcount(self->response, > 0);
    
  // smisk.core.response = self.response
  objproxy = PyObject_GetAttrString(smisk_core_module, "response");
  rc = PyObject_CallMethod(objproxy, "_set_object", "O", (PyObject *)self->response);
  Py_DECREF(objproxy);
  if (rc == NULL)
    return -1;
  Py_DECREF(rc);
  
  return 0;
}


static int _fork(smisk_Application *self) {
  log_trace("ENTER");
  int i = 0;
  pid_t pid;
  
  if (self->fork_pids) {
    free(self->fork_pids);
    self->fork_pids = NULL;
  }
  
  for (; i<self->forks; i++) {
    pid = fork();
    
    if (pid == -1) {
      log_error("fork() failed");
      PyErr_SET_FROM_ERRNO;
      return -1;
    }
    else if (pid == 0) {
      // child
      log_debug("New child process started");
      PyOS_AfterFork();
      return 1;
    }
    else {
      // parent
      if (self->fork_pids == NULL)
        self->fork_pids = (pid_t *)malloc(sizeof(pid_t)*self->forks);
      self->fork_pids[i] = pid;
    }
  }
  log_trace("EXIT");
  return 0;
}


static int _wait_for_child_procs(smisk_Application *self) {
  log_trace("ENTER");
  int i = 0, child_exit_status;
  for (; i < self->forks; i++) {
    waitpid(self->fork_pids[i], &child_exit_status, 0);
#if SMISK_DEBUG
    if (WIFEXITED(child_exit_status)) {
      log_debug("child %d exited with status %d", 
        self->fork_pids[i], WEXITSTATUS(child_exit_status));
    }
    else if (WIFSIGNALED(child_exit_status)) {
      log_debug("child %d exited due to signal %d", 
        self->fork_pids[i], WTERMSIG(child_exit_status));
    }
    else if (WIFSTOPPED(child_exit_status)) {
      log_debug("child %d is stopped",
        self->fork_pids[i]);
    }
    else {
      log_debug("child %d terminated abnormally. waitpid() returned 0x%x",
        self->fork_pids[i], child_exit_status);
    }
#endif
  }
  log_trace("EXIT");
  return 0;
}


// signal handlers wrapping run method

int smisk_Application_trapped_signal = 0;

static void _sighandler_close_fcgi(int sig) {
  log_trace("ENTER");
  log_debug("Caught signal %d", sig);
  smisk_Application_trapped_signal = sig;
  FCGX_ShutdownPending();
}


#pragma mark -
#pragma mark Initialization & deallocation

PyObject * smisk_Application_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {
  log_trace("ENTER");
  smisk_Application *self;
  PyObject *objproxy, *rc;
  
  self = (smisk_Application *)type->tp_alloc(type, 0);
  if (self != NULL) {
    // Set default classes
    self->request_class = (PyTypeObject*)&smisk_RequestType;
    self->response_class = (PyTypeObject*)&smisk_ResponseType;
    self->sessions_class = (PyTypeObject*)&smisk_FileSessionStoreType;
  
    // Set transaction context to None - run() will set up these.
    self->request = (smisk_Request *)Py_None; Py_INCREF(Py_None);
    self->response = (smisk_Response *)Py_None; Py_INCREF(Py_None);
    
    // Nullify lazy objects
    self->sessions = NULL;
  
    // Default values
    self->show_traceback = Py_True; Py_INCREF(Py_True);
    self->forks = 0;
    self->charset = kString_utf_8; Py_INCREF(kString_utf_8);
    self->fork_pids = NULL;
    
    // Application.current = self
    smisk_Application_set_current((PyObject *)self);
    
    // smisk.core.app = self
    objproxy = PyObject_GetAttrString(smisk_core_module, "app");
    rc = PyObject_CallMethod(objproxy, "_set_object", "O", (PyObject *)self);
    Py_DECREF(objproxy);
    if (rc == NULL)
      return NULL;
    Py_DECREF(rc);
  }
  
  return (PyObject *)self;
}


int smisk_Application_init(smisk_Application *self, PyObject *args, PyObject *kwargs) {
  return 0;
}


void smisk_Application_dealloc(smisk_Application *self) {
  log_trace("ENTER");
  
  if (smisk_Application_current == self)
    smisk_Application_set_current(Py_None);
  
  Py_DECREF(self->request);
  Py_DECREF(self->response);
  Py_XDECREF(self->sessions);
  Py_DECREF(self->show_traceback);
  Py_DECREF(self->charset);
  
  if (self->fork_pids)
    free(self->fork_pids);
  
  self->ob_type->tp_free((PyObject*)self);
}


#pragma mark -
#pragma mark Methods


PyDoc_STRVAR(smisk_Application_run_DOC,
  "Run application.\n"
  "\n"
  ":rtype: None");
PyObject *smisk_Application_run(smisk_Application *self) {
  log_trace("ENTER");
  int rc, is_child_process = 0;
  PyOS_sighandler_t orig_int_handler, orig_hup_handler, orig_term_handler, orig_sigusr1_handler;
  PyObject *ret = Py_None;
  
  // Fork
  if ( (self->forks > 0) && ( (is_child_process = _fork(self)) == -1) )
    return NULL;
  
  // Set program name to argv[0]
  PyObject *argv = PySys_GetObject("argv");
  if (PyList_GET_SIZE(argv))
    Py_SetProgramName(basename(PyBytes_AsString(PyList_GetItem(argv, 0))));
  
  // Setup request object
  FCGX_Request request;
  FCGX_InitRequest(&request, smisk_listensock_fileno, FCGI_FAIL_ACCEPT_ON_INTR);
  
  // Register signal handlers
  orig_int_handler = PyOS_setsig(SIGINT, _sighandler_close_fcgi);
  orig_hup_handler = PyOS_setsig(SIGHUP, _sighandler_close_fcgi);
  orig_term_handler = PyOS_setsig(SIGTERM, _sighandler_close_fcgi);
  orig_sigusr1_handler = PyOS_setsig(SIGUSR1, _sighandler_close_fcgi);
  
  // CGI test
  if (FCGX_IsCGI() && (smisk_listensock_fileno == FCGI_LISTENSOCK_FILENO))
    return PyErr_Format(PyExc_EnvironmentError, "Application must be run in a FastCGI environment");
  
  // Create transaction context
  if (_setup_transaction_context(self) != 0)
    return NULL;
  
  // Notify ourselves we are about to start accepting requests
  if (PyObject_CallMethod((PyObject *)self, "application_will_start", NULL) == NULL)
    return NULL;
  
  // Enter accept loop
  rc = 0;
  while (rc == 0) {
    EXTERN_OP(rc = FCGX_Accept_r(&request));
    if (rc != 0) {
      log_debug("FCGX_Accept_r failed (normal during shutdown)");
      break;
    }
    
    if (smisk_Application_trapped_signal)
      break;
    
    log_debug("%s %s from %s:%s",
      FCGX_GetParam("REQUEST_METHOD", request.envp),
      FCGX_GetParam("REQUEST_URI", request.envp),
      FCGX_GetParam("REMOTE_ADDR", request.envp),
      FCGX_GetParam("REMOTE_PORT", request.envp) );
    
    // Set streams
    self->request->input->stream  = request.in;
    self->response->out->stream   = request.out;
    self->request->errors->stream = request.err;
    self->request->envp           = request.envp;
    
    // Service request
    if (PyObject_CallMethod((PyObject *)self, "service", NULL) != NULL) {
      // Finish response
      smisk_Response_finish(self->response);
      // We do not catch errors here because we PyErr_Occurred later
    }
    #if SMISK_DEBUG
      else if (!smisk_Application_trapped_signal) {
        PyObject *repr = PyObject_Repr((PyObject *)self);
        log_debug("%s.service() failed", PyBytes_AsString(repr));
        Py_DECREF(repr);
      }
    #endif
    
    // Exception raised?
    if (PyErr_Occurred()) {
      if (smisk_Application_trapped_signal) {
        PyErr_Print();
        break;
      }
      else {
        PyObject *type, *value, *tb;
        PyErr_Fetch(&type, &value, &tb); // will also clear
        
        // DEBUG: log exception to stderr
        #if SMISK_DEBUG
          PyObject *type_repr, *value_repr, *tb_repr;
          type_repr = PyObject_Repr((PyObject *)type);
          value_repr = PyObject_Repr((PyObject *)value);
          tb_repr = PyObject_Repr((PyObject *)tb);
          log_debug("Exeption: type=%s, value=%s, tb=%s", PyBytes_AsString(type_repr),
                    PyBytes_AsString(value_repr), PyBytes_AsString(tb_repr));
          Py_DECREF(type_repr);
          Py_DECREF(value_repr);
          Py_DECREF(tb_repr);
        #endif
        
        PyObject *err_ret = PyObject_CallMethod((PyObject *)self, "error", "OOO", type, value, tb);
        Py_DECREF(type);
        Py_DECREF(value);
        Py_DECREF(tb);
        if (err_ret != NULL) {
          Py_DECREF(err_ret);
          smisk_Response_finish(self->response);
          if (PyErr_Occurred())
            PyErr_Clear();
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
    if ( (smisk_Request_reset(self->request) != 0) || (smisk_Response_reset(self->response) != 0) ) {
      log_debug("Reqeust.reset() or Response.reset() failed");
      PyErr_Print();
      raise(SIGINT);
    }
  }
  
  // Notify ourselves we have stopped accepting requests
  if (PyObject_CallMethod((PyObject *)self, "application_did_stop", NULL) == NULL)
    return NULL;
  
  request.keepConnection = 0; // make sure streams are closed.
  EXTERN_OP(FCGX_Finish_r(&request));
  
  // reset signal handlers
  PyOS_setsig(SIGINT, orig_int_handler);
  PyOS_setsig(SIGHUP, orig_hup_handler);
  PyOS_setsig(SIGTERM, orig_term_handler);
  PyOS_setsig(SIGUSR1, orig_sigusr1_handler);
  
  // Now, raise the signal again if that was the reason for exiting the
  // run loop, unless SIGUSR1.
  if (smisk_Application_trapped_signal != 0) {
    if (smisk_Application_trapped_signal != SIGUSR1) {
      log_debug("raising signal %d again", smisk_Application_trapped_signal);
      raise(smisk_Application_trapped_signal);
    }
    smisk_Application_trapped_signal = 0;
  }
  
  // Wait for child processes to exit
  if ( (self->forks > 0) && (!is_child_process) && (_wait_for_child_procs(self) != 0) )
    return NULL;
  
  if (ret == Py_None)
    Py_INCREF(ret);
  
  log_trace("EXIT");
  return ret;
}


PyDoc_STRVAR(smisk_Application_service_DOC,
  "Service a request.\n"
  "\n"
  ":rtype: None");
PyObject *smisk_Application_service(smisk_Application *self, PyObject *args) {
  log_trace("ENTER");
  
  EXTERN_OP(
    FCGX_FPrintF(self->response->out->stream,
     "Content-type: text/html\r\n"
     "\r\n"
     "<html><head><title>Smisk instance #%d</title></head><body>"
     "<h1>Smisk instance #%d</h1>\n"
     "No services available"
     "</body></html>\n", getpid(), getpid());
  )
  
  Py_RETURN_NONE;
}


PyDoc_STRVAR(smisk_Application_error_DOC,
  "Handle an error and produce an appropriate response.\n"
  "\n"
  "The built-in implementation renders error information as XHTML encoded "
    "in UTF-8 with the HTTP status code 500 (Internal Server Error).\n"
  "\n"
  "You might override this to display a custom error response, but it is "
    "recommended you use this implementation, or at least filter certain "
    "higher level exceptions and let the lower ones through to this handler.\n"
  "\n"
  "Normally, this is what you do::\n"
  "\n"
  " class MyApp(Application):\n"
  "   def error(self, typ, val, tb):\n"
  "     if isinstance(val, MyExceptionType):\n"
  "       self.nice_error_response(typ, val)\n"
  "     else:\n"
  "       Application.error(self, typ, val, tb)\n"
  "\n"
  "What is sent as response depends on if output has started or not: If "
    "output has started, if `Response.has_begun` is ``True``, calling this "
    "method will insert a HTML formatted error message at the end of what "
    "has already been sent. If output has not yet begun, any headers set "
    "will be discarded and a complete HTTP response will be sent, including "
    "the same HTML message describet earlier.\n"
  "\n"
  "If `show_traceback` evaluates to true, the error message will also include "
    "a somewhat detailed backtrace. You should disable `show_traceback` in "
    "production environments.\n"
  "\n"
  ":see:  `Response.has_begun`\n"
  ":param typ: Exception type\n"
  ":type  typ: type\n"
  ":param val: Exception value\n"
  ":type  val: Exception\n"
  ":param tb:  Traceback\n"
  ":type  tb:  object\n"
  ":rtype: None");
PyObject *smisk_Application_error(smisk_Application *self, PyObject *args) {
  log_trace("ENTER");
  
  int rc, free_hostname = 0;
  PyObject *msg, *exc_str, *type, *value, *tb;
  char *exc_strp = NULL, 
       *value_repr = NULL, 
       *hostname = NULL,
       *port = NULL;
  
  if (!PyArg_UnpackTuple(args, "error", 3, 3, &type, &value, &tb))
    return NULL;
  
  // Format exception into string
  if ( (exc_str = smisk_format_exc(type, value, tb)) == NULL )
    return NULL;
  
  if (!self->request) {
    PyErr_SetString(PyExc_EnvironmentError, "self->request == NULL");
    return NULL;
  }
  
  ENSURE_BY_GETTER(self->request->env, smisk_Request_get_env(self->request),
    return NULL;
  );
  
  // Get reference to last line of trace, containing short message
  exc_strp = PyBytes_AsString(exc_str);
  Py_ssize_t len = PyBytes_Size(exc_str)-2;
  for (; len; len-- ) {
    if (exc_strp[len] == '\n') {
      log_debug("%s", exc_strp+len);
      value_repr = exc_strp+len;
      break;
    }
  }
  
  // Get SERVER_NAME and separate port if any
  // Beyond this point, you must not simply return, but check free_hostname
  // goto return_error_from_errno is available as a convenience.
  if ((hostname = FCGX_GetParam("SERVER_NAME", self->request->envp))) {
    if ( (port = strchr(hostname, (int)':')) ) {
      size_t len = port-hostname;
      char *buf = (char *)malloc(len+1);
      strncpy(buf, hostname, len);
      buf[len] = 0;
      port++;
      hostname = buf;
      free_hostname = 1;
    }
  }
  
  // Set port if not already set
  if (!port)
    port = FCGX_GetParam("SERVER_PORT", self->request->envp);
  
  // Format error message
  msg = PyBytes_FromFormat("<h1>Service Error</h1>\n"
    "<p class=\"message\">%s</p>\n"
    "<pre class=\"traceback\">%s</pre>\n"
    "<hr/><address>%s at %s port %s</address>\n",
    value_repr ? value_repr : "",
    ((self->show_traceback == Py_True) ? exc_strp : "Additional information has been logged."),
    PyBytes_AsString(PyDict_GetItemString(self->request->env, "SERVER_SOFTWARE")),
    hostname ? hostname : "?",
    port ? port : "?");
  
  // Log exception throught fcgi error stream
  EXTERN_OP(
    rc = FCGX_PutStr(PyBytes_AsString(exc_str), 
                     PyBytes_Size(exc_str),
                     self->request->errors->stream)
  );
  if (rc == -1) {
    // Fall back to stderr
    log_error("Error in %s.error(): %s",
      PyBytes_AsString(PyObject_Str((PyObject *)self)),
      PyBytes_AsString(exc_str));
    goto return_error_from_errno;
  }
  
  Py_DECREF(exc_str);
  
  if (self->response->has_begun == Py_False) {
    // Include headers if response has not yet been sent
    static char *header = "<html><head>"
      "<title>Service Error</title>"
      "<style type=\"text/css\">\n"
        "body,html { padding:0; margin:0; background:#666; }\n"
        "h1 { padding:25pt 10pt 10pt 15pt; background:#ffb2bf; color:#560c00; "
             "font-family:arial,helvetica,sans-serif; margin:0; }\n"
        "address, p { font-family:'lucida grande',verdana,arial,sans-serif; }\n"
        "p.message { padding:10pt 16pt; background:#fff; color:#222; margin:0; font-size:.9em; }\n"
        "pre.traceback { padding:10pt 15pt 25pt 15pt; line-height:1.4; "
                        "background:#f2f2ca; color:#52523b; "
                        "margin:0; border-top:1px solid #e3e3ba; border-bottom:1px solid #555; }\n"
        "hr { display:none; }\n"
        "address { padding:10pt 15pt; color:#333; font-size:11px; }\n"
      "</style>"
      "</head><body>";
    static char *footer = "</body></html>";
    EXTERN_OP(
      rc = FCGX_FPrintF(self->response->out->stream,
        "Status: 500 Internal Server Error\r\n"
        "Content-Type: text/html; charset=utf-8\r\n"
        "Content-Length: %ld\r\n"
        "Cache-Control: no-cache\r\n"
         "\r\n"
         "%s%s%s\r\n",
        // we know this is a normal string, thus no unicode support
        strlen(header)+PyBytes_GET_SIZE(msg)+strlen(footer)+2,
        header,
        PyBytes_AS_STRING(msg), 
        footer);
    );
  }
  else {
    // we know this is a normal string, thus no unicode support
    EXTERN_OP( rc = FCGX_PutStr(PyBytes_AS_STRING(msg),
                                PyBytes_GET_SIZE(msg),
                                self->response->out->stream) );
  }
  
  Py_DECREF(msg);
  
  if (rc == -1)
    goto return_error_from_errno;
  
  if (free_hostname)
    free(hostname);
  Py_RETURN_NONE;
  
return_error_from_errno:
  if (free_hostname)
    free(hostname);
  return PyErr_SET_FROM_ERRNO;
}


PyDoc_STRVAR(smisk_Application_exit_DOC,
  "Exit application.\n"
  "\n"
  ":rtype: None");
PyObject *smisk_Application_exit(smisk_Application *self) {
  log_trace("ENTER");
  raise(SIGUSR1);
  Py_RETURN_NONE;
}


#pragma mark -
#pragma mark Notification methods


PyDoc_STRVAR(smisk_Application_application_will_start_DOC,
  "Called just before the application starts accepting incoming requests.\n"
  "\n"
  "The default implementation in `smisk.core.Application` does nothing.\n"
  "\n"
  ":rtype: None");
PyObject *smisk_Application_application_will_start(smisk_Application *self) {
  log_trace("ENTER");
  Py_RETURN_NONE;
}


PyDoc_STRVAR(smisk_Application_application_did_stop_DOC,
  "Called when the application stops accepting incoming requests.\n"
  "\n"
  "The default implementation in `smisk.core.Application` does nothing.\n"
  "\n"
  ":rtype: None");
PyObject *smisk_Application_application_did_stop(smisk_Application *self) {
  log_trace("ENTER");
  Py_RETURN_NONE;
}


#pragma mark -
#pragma mark Properties

PyObject *smisk_Application_get_sessions(smisk_Application* self) {
  log_trace("ENTER");
  if (self->sessions == NULL) {
    IFDEBUG(DUMP_REPR(self->sessions_class));
    if ((self->sessions = PyObject_Call((PyObject*)self->sessions_class, NULL, NULL)) == NULL)
      return NULL;
    
    log_debug("self->sessions=%p", self->sessions);
  }
  
  Py_INCREF(self->sessions); // callers reference
  return self->sessions;
}


static int smisk_Application_set_sessions(smisk_Application* self, PyObject *sessions) {
  log_trace("ENTER  sessions=%p", sessions);
  REPLACE_OBJ(self->sessions, sessions, PyObject);
  return self->sessions ? 0 : -1;
}



PyObject *smisk_Application_get_charset(smisk_Application* self) {
  log_trace("ENTER");
  Py_INCREF(self->charset); // callers reference
  return self->charset;
}


static int smisk_Application_set_charset(smisk_Application* self, PyObject *charset) {
  log_trace("ENTER");
  PyObject* old = self->charset;
  self->charset = PyObject_Str(charset);
  Py_XDECREF(old);
  
  if (!self->charset)
    return -1;
  
  if ( ((PyObject *)self->request) != Py_None )
    Py_CLEAR(self->request->get);
  
  // Note: We can not remove lazy POST because the original data is
  //       no longer available after initial parsing.
  
  return 0;
}


/********** type configuration **********/

PyDoc_STRVAR(smisk_Application_DOC,
  "An application");

// Methods
static PyMethodDef smisk_Application_methods[] = {
  // Instance
  {"run",     (PyCFunction)smisk_Application_run,     METH_NOARGS, smisk_Application_run_DOC},
  {"service", (PyCFunction)smisk_Application_service, METH_VARARGS, smisk_Application_service_DOC},
  {"error",   (PyCFunction)smisk_Application_error,   METH_VARARGS, smisk_Application_error_DOC},
  {"exit",    (PyCFunction)smisk_Application_exit,    METH_NOARGS,  smisk_Application_exit_DOC},
  
  // Instance (Notifications)
  {"application_will_start",  (PyCFunction)smisk_Application_application_will_start,
    METH_NOARGS,  smisk_Application_application_will_start_DOC},
  {"application_did_stop",    (PyCFunction)smisk_Application_application_did_stop,
    METH_NOARGS,  smisk_Application_application_did_stop_DOC},
  
  {NULL, NULL, 0, NULL}
};

// Properties
static PyGetSetDef smisk_Application_getset[] = {
  {"sessions",
    (getter)smisk_Application_get_sessions,
    (setter)smisk_Application_set_sessions,
    ":type: `smisk.session.Store`", NULL},
  
  {"charset",
    (getter)smisk_Application_get_charset,
    (setter)smisk_Application_set_charset,
    "Sets the character encoding used for GET/POST accesses. If the GET or POST "
    "dictionary has already been created, it is removed and recreated on the "
    "next access (so that it is decoded correctly). "
    "Defaults to 'utf-8'", NULL},
  
  {NULL, NULL, NULL, NULL, NULL}
};

// Members
static struct PyMemberDef smisk_Application_members[] = {
  {"request_class",  T_OBJECT_EX, offsetof(smisk_Application, request_class), 0,
    ":type: Type\n\n"
    "Must be set before calling `run()`"},
  
  {"response_class", T_OBJECT_EX, offsetof(smisk_Application, response_class), 0,
    ":type: Type\n\n"
    "Must be set before calling `run()`"},
  
  {"sessions_class",  T_OBJECT_EX, offsetof(smisk_Application, sessions_class), 0,
    ":type: Type\n\n"
    "Must be set before first access to `sessions`"},
  
  {"request",  T_OBJECT_EX, offsetof(smisk_Application, request),  RO,
    ":type: `Request`"},
  
  {"response", T_OBJECT_EX, offsetof(smisk_Application, response), RO,
    ":type: `Response`"},
  
  {"show_traceback", T_OBJECT_EX, offsetof(smisk_Application, show_traceback), 0,
    ":type: bool\n\n"
    "Defaults to True."},
  
  {"forks", T_INT, offsetof(smisk_Application, forks), 0,
    ":type: int\n\n"
    "Number of child processes to fork off into.\n"
    "\n"
    "*Note:* Forking is experimental and needs testing.\n"
    "\n"
    "This must be set before calling `run()`, as it's in `run()` where the "
    "forking goes down. Defaults to 0 (disabled)."},
  
  {NULL, 0, 0, 0, NULL}
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
  log_trace("ENTER");
  if (smisk_Application_current == NULL) {
    smisk_Application_current = (smisk_Application *)Py_None;
    Py_INCREF(Py_None);
  }
  if (PyType_Ready(&smisk_ApplicationType) == 0) {
    if(PyModule_AddObject(module, "Application", (PyObject *)&smisk_ApplicationType) == 0) {
      return SMISK_PyObject_SET(&smisk_ApplicationType, "current", smisk_Application_current);
    }
  }
  return -1;
}
