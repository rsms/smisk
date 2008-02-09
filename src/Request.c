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
#include "Request.h"
#include <structmember.h>
#include <fastcgi.h>

int smisk_Request_init(smisk_Request* self, PyObject* args, PyObject* kwargs)
{
  DLog("ENTER smisk_Request_init");
  
  // Set env to None
  self->env = Py_None;
  Py_INCREF(self->env);
  
  // Set _url to NULL
  self->url = NULL;
  
  // Construct a new Stream for in
  self->input = (smisk_Stream*)PyObject_Call((PyObject*)&smisk_StreamType, NULL, NULL);
  if (self->input == NULL) {
    DLog("self->input == NULL");
    Py_DECREF(self);
    return -1;
  }
  
  // Construct a new Stream for err
  self->err = (smisk_Stream*)PyObject_Call((PyObject*)&smisk_StreamType, NULL, NULL);
  if (self->err == NULL) {
    DLog("self->err == NULL");
    Py_DECREF(self);
    return -1;
  }
  
  return 0;
}

// Called by Application.run just after a successful accept() 
// and just before calling service().
int smisk_Request_reset (smisk_Request* self) {
  if(self->env && (self->env != Py_None)) {
    Py_DECREF(self->env);
    self->env = NULL;
  }
  
  if(self->url && ((PyObject *)self->url != Py_None)) {
    Py_DECREF(self->url);
    self->url = NULL;
  }
  
  return 0;
}

void smisk_Request_dealloc(smisk_Request* self)
{
  DLog("ENTER smisk_Request_dealloc");
  
  Py_XDECREF(self->input);
  Py_XDECREF(self->err);
  Py_XDECREF(self->env);
  
  // free envp buf
  if(self->envp_buf)
    free(self->envp_buf);
}


PyDoc_STRVAR(smisk_Request_log_error_DOC,
  "Log something through self.err including process name and id.\n"
  "\n"
  "Normally, self.err ends up in the host server error log.\n"
  ":param  message:  Message to log\n"
  ":type   filename: string\n"
  ":raises smisk.IOError: if something i/o failed.\n"
  ":rtype: None");
PyObject* smisk_Request_log_error(smisk_Request* self, PyObject* args) {
  PyObject* message;
  static const char format[] = "%s[%d] %s";
  
  // Did we get enough arguments?
  if(PyTuple_GET_SIZE(args) != 1) {
    PyErr_SetString(PyExc_TypeError, "logError takes exactly 1 argument");
    return NULL;
  }
  
  // Save reference to first argument and type check it
  message = PyTuple_GET_ITEM(args, 0);
  if(!PyString_Check(message)) {
    PyErr_SetString(PyExc_TypeError, "first argument must be a string");
    return NULL;
  }
  
  if(FCGX_FPrintF( self->err->stream, format, 
    Py_GetProgramName(), getpid(), PyString_AsString(message)) == -1)
  {
    fprintf(stderr, format, 
      Py_GetProgramName(), getpid(), PyString_AsString(message));
    return PyErr_SET_FROM_ERRNO_OR_CUSTOM(smisk_IOError, "Failed to write on stream");
  }
  
  Py_RETURN_NONE;
}


PyObject* smisk_Request_get_env(smisk_Request* self) {
  //DLog("ENTER smisk_Request_get_env");
  
  // Lazy initializer
  if(self->env == Py_None || !self->env) {
    
    // Alloc new dict
    self->env = PyDict_New();
    if(self->env == NULL) {
      DLog("self->env == NULL");
      return NULL;
    }
    
    // Transcribe envp to dict
    if(self->envp != NULL) {
      
      PyStringObject* k;
      PyStringObject* v;
      char** envp = self->envp; // Need operate on new pointer or FCGX_* will crash
      
      // Parse env into dict
      for( ; *envp != NULL; envp++) {
        
        char *value = strchr(*envp, '=');
        
        if(!value) {
          DLog("Strange item in ENV (missing '=')");
          continue;
        }
        
        k = (PyStringObject *)PyString_FromStringAndSize(*envp, value-*envp);
        if(k == NULL) {
          DLog("ERROR: Failed to create string");
          break;
        }
        
        v = (PyStringObject *)PyString_FromString(++value);
        if(v == NULL) {
          DLog("ERROR: Failed to create string");
          Py_DECREF(k);
          break;
        }
        
        if( PyDict_SetItem( (PyObject *)self->env, (PyObject *)k, (PyObject *)v) )
        {
          DLog("PyDict_SetItem() != 0");
          return NULL;
        }
        
        Py_DECREF(k);
        Py_DECREF(v);
      }
    }
    
    // Make read-only
    //self->env = (PyDictObject*)PyDictProxy_New((PyObject*)self->env);
  }
  
  Py_INCREF(self->env);
  return (PyObject*)self->env;
}


// This should only be used internally and for strings we are certain
// only contain characters within ASCII.
inline char *_strtolower(char *s) {
  char *p = s;
  do {
    *p = tolower(*p);
  } while( *p++ );
  return s;
}


PyObject* smisk_Request_get_url(smisk_Request* self) {
  char *s, *p, *s2;
  
  if(self->url == NULL) {
    if (!(self->url = (smisk_URL*)PyObject_Call((PyObject*)&smisk_URLType, NULL, NULL))) {
      DLog("self->url == NULL");
      return NULL;
    }
    
    // Scheme
    if((s = FCGX_GetParam("SERVER_PROTOCOL", self->envp)) && (p = strchr(s, '/'))) {
      *p = '\0';
      Py_DECREF(self->url->scheme);
      self->url->scheme = PyString_FromString(_strtolower(s));
      Py_INCREF(self->url->scheme);
    }
    
    // User
    if(s = FCGX_GetParam("REMOTE_USER", self->envp)) {
      Py_DECREF(self->url->user);
      Py_INCREF(self->url->user);
      self->url->user = PyString_FromString(s);
      Py_INCREF(self->url->user);
    }
    
    // Host & port
    s = FCGX_GetParam("SERVER_NAME", self->envp);
    Py_DECREF(self->url->host);
    if((p = strchr(s, ':'))) {
      self->url->host = PyString_FromStringAndSize(s, p-s);
      self->url->port = atoi(p+1);
    }
    else if(s2 = FCGX_GetParam("SERVER_PORT", self->envp)) {
      self->url->host = PyString_FromString(s);
      self->url->port = atoi(s2);
    }
    else {
      self->url->host = PyString_FromString(s);
    }
    Py_INCREF(self->url->host);
    
    // Path & querystring
    // Not in RFC, but considered standard
    if(s = FCGX_GetParam("REQUEST_URI", self->envp)) {
      Py_DECREF(self->url->path);
      if(p = strchr(s, '?')) {
        *p = '\0';
        self->url->path = PyString_FromString(s);
        Py_DECREF(self->url->query);
        self->url->query = PyString_FromString(p+1);
        Py_INCREF(self->url->query);
      }
      else {
        self->url->path = PyString_FromString(s);
      }
      Py_INCREF(self->url->path);
    }
    // Non-REQUEST_URI compliant fallback
    else {
      if(s = FCGX_GetParam("SCRIPT_NAME", self->envp)) {
        Py_DECREF(self->url->path);
        self->url->path = PyString_FromString(s);
        Py_INCREF(self->url->path);
        // May not always give the same results as the above implementation
        // because the CGI specification does claim "This information should be
        // decoded by the server if it comes from a URL" which is a bit vauge.
        if(s = FCGX_GetParam("PATH_INFO", self->envp)) {
          PyString_Concat(&self->url->path, PyString_FromString(s));
        }
      }
      if(s = FCGX_GetParam("QUERY_STRING", self->envp)) {
        Py_DECREF(self->url->query);
        self->url->query = PyString_FromString(s);
        Py_INCREF(self->url->query);
      }
    }
    
    Py_INCREF(self->url);
  }
  
  return (PyObject *)self->url;
}


/********** type configuration **********/

PyDoc_STRVAR(smisk_Request_DOC,
  "A FastCGI request\n"
  "\n"
  ":ivar input:  Input stream\n"
  ":type input:  smisk.Stream\n"
  ":ivar err:    Error output stream\n"
  ":type err:    smisk.Stream\n"
  ":ivar url:    Reconstructed URL. (Lazy initialized)\n"
  ":type url:    smisk.URL\n"
  ":ivar env:    Request parameters, equivalent to the ``env`` in CGI. (Lazy initialized)\n"
  ":type env:    dict");

// Methods
static PyMethodDef smisk_Request_methods[] =
{
  {"log_error", (PyCFunction)smisk_Request_log_error, METH_VARARGS, smisk_Request_log_error_DOC},
  {NULL}
};

// Properties
static PyGetSetDef smisk_Request_getset[] = {
    {"env", (getter)smisk_Request_get_env, (setter)0},
    {"url", (getter)smisk_Request_get_url, (setter)0},
    {NULL}
};

// Class members
static struct PyMemberDef smisk_Request_members[] =
{
  {"input", T_OBJECT_EX, offsetof(smisk_Request, input), RO, NULL},
  {"err",   T_OBJECT_EX, offsetof(smisk_Request, err),   RO, NULL},
  {NULL}
};

// Type definition
PyTypeObject smisk_RequestType = {
  PyObject_HEAD_INIT(&PyType_Type)
  0,                         /*ob_size*/
  "smisk.Request",             /*tp_name*/
  sizeof(smisk_Request),       /*tp_basicsize*/
  0,                         /*tp_itemsize*/
  (destructor)smisk_Request_dealloc,        /* tp_dealloc */
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
  smisk_Request_DOC,          /*tp_doc*/
  (traverseproc)0,           /* tp_traverse */
  0,                         /* tp_clear */
  0,                         /* tp_richcompare */
  0,                         /* tp_weaklistoffset */
  0,                         /* tp_iter */
  0,                         /* tp_iternext */
  smisk_Request_methods,      /* tp_methods */
  smisk_Request_members,      /* tp_members */
  smisk_Request_getset,         /* tp_getset */
  0,                           /* tp_base */
  0,                           /* tp_dict */
  0,                           /* tp_descr_get */
  0,                           /* tp_descr_set */
  0,                           /* tp_dictoffset */
  (initproc)smisk_Request_init, /* tp_init */
  0,                           /* tp_alloc */
  PyType_GenericNew,           /* tp_new */
  0                            /* tp_free */
};

extern int smisk_Request_register_types(void)
{
    return PyType_Ready(&smisk_RequestType);
}
