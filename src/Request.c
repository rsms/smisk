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
#include "multipart.h"
#include "Request.h"
#include <unistd.h>
#include <structmember.h>
#include <fastcgi.h>


static char *smisk_read_fcgxstream(FCGX_Stream *stream, long length) {
  char *s;
  int bytes_read;
  
  if(length == 0) {
    return strdup("");
  }
  else if(length > 0) {
    s = (char *)malloc(length+1);
    bytes_read = FCGX_GetStr(s, length, stream);
    s[(bytes_read < length) ? bytes_read : length] = '\0';
    return s;
  }
  else { // unknown length
    size_t size = SMISK_STREAM_READ_CHUNKSIZE;
    s = (char *)malloc(size);
    
    while(1) {
      bytes_read = FCGX_GetStr(s, SMISK_STREAM_READ_CHUNKSIZE, stream);
      if(bytes_read < SMISK_STREAM_READ_CHUNKSIZE) {
        s[(size - SMISK_STREAM_READ_CHUNKSIZE) + bytes_read] = '\0';
        break; // EOF
      }
      size += SMISK_STREAM_READ_CHUNKSIZE;
      s = (char *)realloc(s, size);
    }
    
    return s;
  }
}


static int _parse_request_body(smisk_Request* self) {
  char *content_type;
  long content_length;
  
  if((self->post = PyDict_New()) == NULL) {
    return -1;
  }
  
  if((self->files = PyDict_New()) == NULL) {
    return -1;
  }
  
  if((content_type = FCGX_GetParam("CONTENT_TYPE", self->envp))) {
    // Parse content-length if available
    char *t = FCGX_GetParam("CONTENT_LENGTH", self->envp);
    content_length = (t != NULL) ? atol(t) : -1;
    
    if(strstr(content_type, "multipart/")) {
      if(smisk_multipart_parse_stream(self->input->stream, content_length, self->post, self->files) != 0) {
        return -1;
      }
    }
    else if(strstr(content_type, "/x-www-form-urlencoded")) {
      char *s = smisk_read_fcgxstream(self->input->stream, content_length);
      int parse_status = parse_input_data(s, "&", 0, self->post);
      free(s);
      if(parse_status != 0) {
        return -1;
      }
    }
    // else, leave it as raw input
  }
  
  return 0;
}


/* ---------------------------------------------- */
/* Python */


int smisk_Request_init(smisk_Request* self, PyObject* args, PyObject* kwargs) {
  log_debug("ENTER smisk_Request_init");
  
  // Nullify lazy instances
  self->env = NULL;
  self->url = NULL;
  self->get = NULL;
  self->post = NULL;
  self->files = NULL;
  self->cookie = NULL;
  
  // Construct a new Stream for in
  self->input = (smisk_Stream*)PyObject_Call((PyObject*)&smisk_StreamType, NULL, NULL);
  if (self->input == NULL) {
    Py_DECREF(self);
    return -1;
  }
  
  // Construct a new Stream for err
  self->err = (smisk_Stream*)PyObject_Call((PyObject*)&smisk_StreamType, NULL, NULL);
  if (self->err == NULL) {
    Py_DECREF(self);
    return -1;
  }
  
  return 0;
}



// Called after every request has finished and called one from Request.dealloc
void smisk_Request_cleanup (smisk_Request* self) {
  // Delete unused uploaded files
  if(self->files) {
    PyObject *files = PyDict_Values(self->files);
    size_t i, count = PyList_GET_SIZE(files);
    for(i=0;i<count;i++) {
      PyObject *file = PyList_GET_ITEM(files, i);
      if(file != Py_None) {
        PyObject *path = PyDict_GetItemString(file, "path");
        if(path) {
          char *fn = PyString_AsString(path);
          if(file_exist(fn) && (unlink(fn) != 0)) {
            log_error("Failed to unlink temporary file %s", fn);
          }
          IFDEBUG(else {
            log_debug("Unlinked unused uploaded file %s", fn);
          });
        }
      }
    }
    Py_DECREF(files);
  }
}


// Called by Application.run just after a successful accept() 
// and just before calling service(). Also called when server stops.
int smisk_Request_reset (smisk_Request* self) {
  smisk_Request_cleanup(self);
  
#define USET(n) if(self->n) { Py_DECREF(self->n); self->n = NULL; }
  USET(env);
  USET(url);
  USET(get);
  USET(post);
  USET(files);
  USET(cookie);
#undef USET
  
  return 0;
}


void smisk_Request_dealloc(smisk_Request* self) {
  log_debug("ENTER smisk_Request_dealloc");
  
  smisk_Request_cleanup(self);
  
  Py_XDECREF(self->input);
  Py_XDECREF(self->err);
  Py_XDECREF(self->env);
  Py_XDECREF(self->url);
  Py_XDECREF(self->get);
  Py_XDECREF(self->post);
  Py_XDECREF(self->files);
  Py_XDECREF(self->cookie);
  
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
  //log_debug("ENTER smisk_Request_get_env");
  
  // Lazy initializer
  if(self->env == NULL) {
    
    // Alloc new dict
    self->env = PyDict_New();
    if(self->env == NULL) {
      log_debug("self->env == NULL");
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
          log_debug("Strange item in ENV (missing '=')");
          continue;
        }
        
        k = (PyStringObject *)PyString_FromStringAndSize(*envp, value-*envp);
        if(k == NULL) {
          log_debug("ERROR: Failed to create string");
          break;
        }
        
        v = (PyStringObject *)PyString_FromString(++value);
        if(v == NULL) {
          log_debug("ERROR: Failed to create string");
          Py_DECREF(k);
          break;
        }
        
        if( PyDict_SetItem(self->env, (PyObject *)k, (PyObject *)v) ) {
          log_debug("PyDict_SetItem() != 0");
          return NULL;
        }
        
        // Release ownership
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
      log_debug("self->url == NULL");
      return NULL;
    }
    
    // Scheme
    if((s = FCGX_GetParam("SERVER_PROTOCOL", self->envp)) && (p = strchr(s, '/'))) {
      *p = '\0';
      Py_DECREF(self->url->scheme);
      self->url->scheme = PyString_FromString(_strtolower(s));
    }
    
    // User
    if((s = FCGX_GetParam("REMOTE_USER", self->envp))) {
      Py_DECREF(self->url->user);
      self->url->user = PyString_FromString(s);
    }
    
    // Host & port
    s = FCGX_GetParam("SERVER_NAME", self->envp);
    Py_DECREF(self->url->host);
    if((p = strchr(s, ':'))) {
      self->url->host = PyString_FromStringAndSize(s, p-s);
      self->url->port = atoi(p+1);
    }
    else if((s2 = FCGX_GetParam("SERVER_PORT", self->envp))) {
      self->url->host = PyString_FromString(s);
      self->url->port = atoi(s2);
    }
    else {
      self->url->host = PyString_FromString(s);
    }
    
    // Path & querystring
    // Not in RFC, but considered standard
    if((s = FCGX_GetParam("REQUEST_URI", self->envp))) {
      Py_DECREF(self->url->path);
      if((p = strchr(s, '?'))) {
        *p = '\0';
        self->url->path = PyString_FromString(s);
        Py_DECREF(self->url->query);
        self->url->query = PyString_FromString(p+1);
      }
      else {
        self->url->path = PyString_FromString(s);
      }
    }
    // Non-REQUEST_URI compliant fallback
    else {
      if((s = FCGX_GetParam("SCRIPT_NAME", self->envp))) {
        Py_DECREF(self->url->path);
        self->url->path = PyString_FromString(s);
        // May not always give the same results as the above implementation
        // because the CGI specification does claim "This information should be
        // decoded by the server if it comes from a URL" which is a bit vauge.
        if((s = FCGX_GetParam("PATH_INFO", self->envp))) {
          PyString_Concat(&self->url->path, PyString_FromString(s));
        }
      }
      if((s = FCGX_GetParam("QUERY_STRING", self->envp))) {
        Py_DECREF(self->url->query);
        self->url->query = PyString_FromString(s);
      }
    }
    
  }
  
  Py_INCREF(self->url);
  return (PyObject *)self->url;
}


PyObject* smisk_Request_get_get(smisk_Request* self) {
  smisk_URL *url;
  
  if(self->get == NULL) {
    if((self->get = PyDict_New()) == NULL) {
      return NULL;
    }
    url = (smisk_URL *)smisk_Request_get_url(self);
    if(url->query && (url->query != Py_None) && (PyString_GET_SIZE(url->query) > 0)) {
      if(parse_input_data(PyString_AS_STRING(url->query), "&", 0, self->get) != 0) {
        Py_DECREF(url);
        return NULL;
      }
    }
    Py_DECREF(url);
  }
  
  Py_INCREF(self->get);
  return self->get;
}


PyObject* smisk_Request_get_post(smisk_Request* self) {
  if(self->post == NULL) {
    if(_parse_request_body(self) != 0) {
      return NULL;
    }
  }
  Py_INCREF(self->post); // callers reference
  return self->post;
}


PyObject* smisk_Request_get_files(smisk_Request* self) {
  if(self->files == NULL) {
    if(_parse_request_body(self) != 0) {
      return NULL;
    }
  }
  Py_INCREF(self->files); // callers reference
  return self->files;
}


PyObject* smisk_Request_get_cookie(smisk_Request* self) {
  char *http_cookie;
  
  if(self->cookie == NULL) {
    if((self->cookie = PyDict_New()) == NULL) {
      return NULL;
    }
    
    if((http_cookie = FCGX_GetParam("HTTP_COOKIE", self->envp))) {
      if(parse_input_data(http_cookie, ";", 1, self->cookie) != 0) {
        return NULL;
      }
    }
  }
  Py_INCREF(self->cookie); // callers reference
  return self->cookie;
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
  {"env", (getter)smisk_Request_get_env,  (setter)0},
  {"url", (getter)smisk_Request_get_url,  (setter)0},
  {"get", (getter)smisk_Request_get_get,  (setter)0},
  {"post", (getter)smisk_Request_get_post, (setter)0},
  {"files", (getter)smisk_Request_get_files,  (setter)0},
  {"cookie", (getter)smisk_Request_get_cookie,  (setter)0},
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
