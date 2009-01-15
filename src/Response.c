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
#include "Response.h"
#include "Application.h"
#include "SessionStore.h"
#include <structmember.h>
#include <ctype.h>
#include <fastcgi.h>

#pragma mark Private C

typedef struct FCGX_Stream_Data {
    unsigned char *buff;      /* buffer after alignment */
    int bufflen;              /* number of bytes buff can store */
    unsigned char *mBuff;     /* buffer as returned by Malloc */
    unsigned char *buffStop;  /* reader: last valid byte + 1 of entire buffer.
                               * stop generally differs from buffStop for
                               * readers because of record structure.
                               * writer: buff + bufflen */
    int type;                 /* reader: FCGI_PARAMS or FCGI_STDIN
                               * writer: FCGI_STDOUT or FCGI_STDERR */
    int eorStop;              /* reader: stop stream at end-of-record */
    int skip;                 /* reader: don't deliver content bytes */
    int contentLen;           /* reader: bytes of unread content */
    int paddingLen;           /* reader: bytes of unread padding */
    int isAnythingWritten;    /* writer: data has been written to ipcFd */
    int rawWrite;             /* writer: write data without stream headers */
    FCGX_Request *reqDataPtr; /* request data not specific to one stream */
} FCGX_Stream_Data;


static int _begin_if_needed(void *_self) {
  smisk_Response *self = (smisk_Response *)_self;
  if ( (self->has_begun == Py_False) && (PyObject_CallMethod((PyObject *)self, "begin", NULL) == NULL) )
    return -1;
  return 0;
}


// Called by Application.run just after a successful accept() 
// and just before calling service().
int smisk_Response_reset (smisk_Response *self) {
  log_trace("ENTER");
  REPLACE_OBJ(self->has_begun, Py_False, PyObject);
  Py_XDECREF(self->headers);
  self->headers = NULL;
  return 0;
}


// Called by Application.run() after a successful call to service()
int smisk_Response_finish(smisk_Response *self) {
  log_trace("ENTER");
  return _begin_if_needed((void *)self);
}


#pragma mark -
#pragma mark Initialization & deallocation


PyObject * smisk_Response_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {
  log_trace("ENTER");
  smisk_Response *self;
  
  if ((self = (smisk_Response *)type->tp_alloc(type, 0)) == NULL)
    return NULL;  
  
  if (smisk_Response_reset(self) != 0) {
    Py_DECREF(self);
    return NULL;
  }
  
  // Construct a new Stream for out
  self->out = (smisk_Stream*)smisk_Stream_new(&smisk_StreamType, NULL, NULL);
  if (self->out == NULL) {
    Py_DECREF(self);
    return NULL;
  }
  
  return (PyObject *)self;
}

int smisk_Response_init(smisk_Response* self, PyObject *args, PyObject *kwargs) {
  log_trace("ENTER");
  return 0;
}

void smisk_Response_dealloc(smisk_Response* self) {
  log_trace("ENTER");
  
  smisk_Response_reset(self);
  
  Py_XDECREF(self->has_begun);
  Py_XDECREF(self->headers);
  Py_XDECREF(self->out);
  
  self->ob_type->tp_free((PyObject*)self);
}


#pragma mark -
#pragma mark Methods


PyDoc_STRVAR(smisk_Response_send_file_DOC,
  "Send a file to the client by using the host server sendfile-header technique.");
PyObject *smisk_Response_send_file(smisk_Response* self, PyObject *filename) {
  log_trace("ENTER");
  PyObject *s = NULL;
  char *server = NULL;
  
  if (!filename || !SMISK_STRING_CHECK(filename))
    return PyErr_Format(PyExc_TypeError, "first argument must be a string");
  
  if (self->has_begun == Py_True)
    return PyErr_Format(PyExc_EnvironmentError, "output has already begun");
  
  if (smisk_Application_current)
    server = FCGX_GetParam("SERVER_SOFTWARE", smisk_Application_current->request->envp);
  
  if (server == NULL)
    server = "unknown server software";
  
  if (strstr(server, "lighttpd/1.4")) {
    s = PyString_FromString("X-LIGHTTPD-send-file: ");
    log_debug("Adding \"X-LIGHTTPD-send-file: %s\" header for Lighttpd <=1.4",
      PyString_AsString(filename));
  }
  else if (strstr(server, "lighttpd/") || strstr(server, "Apache/2")) {
    s = PyString_FromString("X-Sendfile: ");
    log_debug("Adding \"X-Sendfile: %s\" header for Lighttpd >=1.5 | Apache >=2",
      PyString_AsString(filename));
  }
  else if (strstr(server, "nginx/")) {
    s = PyString_FromString("X-Accel-Redirect: ");
    log_debug("Adding \"X-Accel-Redirect: %s\" header for Nginx",
      PyString_AsString(filename));
  }
  else {
    return PyErr_Format(PyExc_EnvironmentError, "sendfile not supported by host server ('%s')", server);
  }
  
  // Make sure self->headers is initialized
  ENSURE_BY_GETTER(self->headers, smisk_Response_get_headers(self), return NULL; );
  
  // Add filename
  PyString_Concat(&s, filename);
  if (s == NULL)
    return NULL;
  
  // Append the header
  if (PyList_Append(self->headers, s) != 0) {
    Py_DECREF(s);
    return NULL;
  }
  
  Py_DECREF(s); // the list is the new owner
  
  Py_RETURN_NONE;
}


PyDoc_STRVAR(smisk_Response_begin_DOC,
  "Send headers");
PyObject *smisk_Response_begin(smisk_Response* self) {
  log_trace("ENTER");
  int rc;
  Py_ssize_t num_headers, i;
  
  if (self->has_begun == Py_True)
    return PyErr_Format(PyExc_EnvironmentError, "output has already begun");
  
  // Note: self->headers can be NULL at this point and that's by design.
  IFDEBUG(if (self->headers) 
    assert_refcount(self->headers, > 0);
  )
  
  EXTERN_OP_START;
  
  // Set session cookie?
  if (smisk_Application_current->request->session_id 
    && (smisk_Application_current->request->initial_session_hash == 0))
  {
    log_debug("New session - sending SID with Set-Cookie: %s=%s;Version=1;Path=/",
      PyString_AsString(((smisk_SessionStore *)smisk_Application_current->sessions)->name),
      PyString_AsString(smisk_Application_current->request->session_id));
    // First-time session!
    if (!SMISK_STRING_CHECK(((smisk_SessionStore *)smisk_Application_current->sessions)->name)) {
      PyErr_SetString(PyExc_TypeError, "sessions.name is not a string");
      EXTERN_OP_END;
      return NULL;
    }
    assert(smisk_Application_current->request->session_id);
    FCGX_FPrintF(self->out->stream, "Set-Cookie: %s=%s;Version=1;Path=/\r\n",
      PyString_AsString(((smisk_SessionStore *)smisk_Application_current->sessions)->name),
      PyString_AsString(smisk_Application_current->request->session_id)
    );
  }
  
  // Add smisk to server tag
  // xxx todo: make configurable. But how? Adding it to smisk.core module won't be
  //           good since we have no way of accessing the value directly (if we put
  //           it as a property of the module, we have to do expensive python lookups)
  //           So maybe adding it to Application like Application.current? No, that
  //           will cause the same problem as described earlier, since we have no way
  //           of reading the value without the expensive lookup.
  char *server_software = FCGX_GetParam("SERVER_SOFTWARE", smisk_Application_current->request->envp);
  if (server_software) {
    FCGX_FPrintF(self->out->stream, "Server: %s smisk/%s\r\n", server_software, SMISK_VERSION);
  }
  else {
    FCGX_FPrintF(self->out->stream, "Server: smisk/%s\r\n", SMISK_VERSION);
  }
  
  // Headers?
  if (self->headers && PyList_Check(self->headers) && (num_headers = PyList_GET_SIZE(self->headers))) {
    // Iterate over headers
    PyObject *str;
    for (i=0;i<num_headers;i++) {
      str = PyList_GET_ITEM(self->headers, i);
      if (str && SMISK_STRING_CHECK(str)) {
        FCGX_PutStr(PyString_AsString(str), PyString_Size(str), self->out->stream);
        FCGX_PutChar('\r', self->out->stream);
        FCGX_PutChar('\n', self->out->stream);
      }
    }
  }
  else {
    // No headers
    FCGX_PutChar('\r', self->out->stream);
    FCGX_PutChar('\n', self->out->stream);
  }
  
  // Header-Body separator
  FCGX_PutChar('\r', self->out->stream);
  rc = FCGX_PutChar('\n', self->out->stream);
  
  EXTERN_OP_END;
  
  REPLACE_OBJ(self->has_begun, Py_True, PyObject);
  
  // Errors?
  if (rc == -1)
    return PyErr_SET_FROM_ERRNO;
  
  log_debug("EXIT smisk_Response_begin");
  Py_RETURN_NONE;
}


PyDoc_STRVAR(smisk_Response_write_DOC,
  "Write to the output stream");
PyObject *smisk_Response_write(smisk_Response* self, PyObject *str) {
  log_trace("ENTER");
  int is_unicode = 0;
  
  if (!str || ( !PyString_Check(str) && !(is_unicode = PyUnicode_Check(str))) )
    return PyErr_Format(PyExc_TypeError, "first argument must be a str or unicode");
  
  // Return immediately if empty string 
  if ( (is_unicode && PyUnicode_GetSize(str) == 0) || (!is_unicode && PyString_Size(str) == 0) )
    Py_RETURN_NONE;
  
  // Encode unicode
  if (is_unicode) {
    str = PyUnicode_AsEncodedString(str, SMISK_APP_CHARSET, "strict");
    if (!str)
      return NULL;
  }
  
  // Send HTTP headers
  if (_begin_if_needed((void *)self) != 0) {
    if (is_unicode) {
      Py_DECREF(str);
    }
    return NULL;
  }
  
  // Write data
  if ( smisk_Stream_perform_write(self->out, str, PyString_Size(str)) == -1 ) {
    if (is_unicode) {
      Py_DECREF(str);
    }
    return NULL;
  }
  
  if (is_unicode) {
    Py_DECREF(str);
  }
  
  Py_RETURN_NONE;
}


PyDoc_STRVAR(smisk_Response_writelines_DOC,
  "Write a sequence of strings to the stream");
PyObject *smisk_Response_writelines(smisk_Response* self, PyObject *sequence) {
  log_trace("ENTER");
  return smisk_Stream_perform_writelines(self->out, sequence, &_begin_if_needed, (void *)self,
    SMISK_APP_CHARSET, "strict");
}


PyObject *smisk_Response___call__(smisk_Response* self, PyObject *args, PyObject *kwargs) {
  log_trace("ENTER");
  // As we can get the length here, we return directly if nothing is to be written.
  if (PyTuple_GET_SIZE(args) < 1)
    Py_RETURN_NONE;
  return smisk_Stream_perform_writelines(self->out, args, &_begin_if_needed, (void *)self,
    SMISK_APP_CHARSET, "strict");
}


PyDoc_STRVAR(smisk_Response_find_header_DOC,
  "Find a headers index in self.headers");
PyObject *smisk_Response_find_header(smisk_Response* self, PyObject *prefix) {
  log_trace("ENTER");
  if (self->headers == NULL)
    return PyInt_FromLong(-1L);
  return smisk_find_string_by_prefix_in_dict(self->headers, prefix);
}


PyDoc_STRVAR(smisk_Response_set_cookie_DOC,
  "Send a cookie");
PyObject *smisk_Response_set_cookie(smisk_Response* self, PyObject *args, PyObject *kwargs) {
  log_trace("ENTER");
  static char *kwlist[] = {"name", "value", /* required */
                           "comment", "domain", "path",
                           "secure", "version", "max_age", "http_only", NULL};
  char *name = NULL,
       *value = NULL,
       *comment = NULL,
       *domain = NULL,
       *path = NULL;
  
  int  secure = 0,
       version = 1,
       max_age = -1,
       http_only = 0;
  
  PyObject *s;
  
  if (self->has_begun == Py_True)
    return PyErr_Format(PyExc_EnvironmentError, "Cookies can not be set when output has already begun.");
  
  if (!PyArg_ParseTupleAndKeywords(args, kwargs, "ss|zzziiii", kwlist,
      &name, &value, &comment, &domain, &path, &secure, &version, &max_age, &http_only)) {
    return NULL;
  }
  
  // Mandatory fields
  
  name = smisk_url_encode(name, strlen(name), 1);
  value = smisk_url_encode(value, strlen(value), 1);
  s = PyString_FromFormat("Set-Cookie: %s=%s;Version=%d", name, value, version);
  free(name); // smisk_url_encode
  free(value); // smisk_url_encode
  
  
  // Optional fields
  
  if (comment) {
    comment = smisk_url_encode(comment, strlen(comment), 1);
    PyString_ConcatAndDel(&s, PyString_FromFormat(";Comment=%s", comment));
    free(comment);
  }
  
  if (domain) {
    domain = smisk_url_encode(domain, strlen(domain), 1);
    PyString_ConcatAndDel(&s, PyString_FromFormat(";Domain=%s", domain));
    free(domain);
  }
  
  if (path) {
    path = smisk_url_encode(path, strlen(path), 1);
    PyString_ConcatAndDel(&s, PyString_FromFormat(";Path=%s", path));
    free(path);
  }
  
  if (max_age > -1) {
    PyString_ConcatAndDel(&s, PyString_FromFormat(";Max-Age=%d", max_age));
    // Add Expires for compatibility reasons
    // ;Expires=Wdy, DD-Mon-YY HH:MM:SS GMT
    // XXX check for NULL returns
    PyObject *expires = PyString_FromStringAndSize(NULL, 36);
    time_t t = time(NULL) + max_age;
    strftime(PyString_AsString(expires), 36, ";Expires=%a, %d-%b-%g %H:%M:%S GMT", gmtime(&t));
    PyString_ConcatAndDel(&s, expires);
  }
  else {
    PyString_ConcatAndDel(&s, PyString_FromString(";Discard"));
  }
  
  if (secure)
    PyString_ConcatAndDel(&s, PyString_FromString(";Secure"));
    
  // More info: http://msdn2.microsoft.com/en-us/library/ms533046(VS.85).aspx
  if (http_only)
    PyString_ConcatAndDel(&s, PyString_FromString(";HttpOnly"));
  
  // Make sure self->headers is initialized
  ENSURE_BY_GETTER(self->headers, smisk_Response_get_headers(self), return NULL; );
  
  // Append the set-cookie header
  if (PyList_Append(self->headers, s) != 0)
    return NULL;
  
  Py_DECREF(s); // the list is the new owner
  
  Py_RETURN_NONE;
}


#pragma mark -
#pragma mark Get- and Setters


PyObject *smisk_Response_get_headers(smisk_Response* self) {
  log_trace("ENTER");
  
  if ( (self->headers == NULL) && ((self->headers = PyList_New(0)) == NULL) )
    return NULL;
  
  Py_INCREF(self->headers); // callers reference
  return self->headers;
}


static int smisk_Response_set_headers(smisk_Response* self, PyObject *headers) {
  log_trace("ENTER");
  REPLACE_OBJ(self->headers, headers, PyObject);
  return self->headers ? 0 : -1;
}


#pragma mark -
#pragma mark Type construction

PyDoc_STRVAR(smisk_Response_DOC,
  "A HTTP response");

// Methods
static PyMethodDef smisk_Response_methods[] = {
  {"send_file",   (PyCFunction)smisk_Response_send_file,    METH_O,       smisk_Response_send_file_DOC},
  {"begin",       (PyCFunction)smisk_Response_begin,        METH_NOARGS,  smisk_Response_begin_DOC},
  {"write",       (PyCFunction)smisk_Response_write,        METH_O,       smisk_Response_write_DOC},
  {"writelines",  (PyCFunction)smisk_Response_writelines,   METH_O,       smisk_Response_writelines_DOC},
  {"set_cookie",  (PyCFunction)smisk_Response_set_cookie,   METH_VARARGS|METH_KEYWORDS,
                  smisk_Response_set_cookie_DOC},
  {"find_header", (PyCFunction)smisk_Response_find_header,  METH_O,       smisk_Response_find_header_DOC},
  {NULL, NULL, 0, NULL}
};

// Properties
static PyGetSetDef smisk_Response_getset[] = {
  {"headers", (getter)smisk_Response_get_headers, (setter)smisk_Response_set_headers, NULL, NULL},
  {NULL, NULL, NULL, NULL, NULL}
};

// Members
static struct PyMemberDef smisk_Response_members[] = {
  {"out",       T_OBJECT_EX, offsetof(smisk_Response, out), RO, NULL},
  {"has_begun", T_OBJECT_EX, offsetof(smisk_Response, has_begun), RO, NULL},
  
  {NULL, 0, 0, 0, NULL}
};

// Type definition
PyTypeObject smisk_ResponseType = {
  PyObject_HEAD_INIT(&PyType_Type)
  0,                         /*ob_size*/
  "smisk.core.Response",             /*tp_name*/
  sizeof(smisk_Response),       /*tp_basicsize*/
  0,                         /*tp_itemsize*/
  (destructor)smisk_Response_dealloc,        /* tp_dealloc */
  0,                         /*tp_print*/
  0,                         /*tp_getattr*/
  0,                         /*tp_setattr*/
  0,                         /*tp_compare*/
  0,                         /*tp_repr*/
  0,                         /*tp_as_number*/
  0,                         /*tp_as_sequence*/
  0,                         /*tp_as_mapping*/
  0,                         /*tp_hash */
  (ternaryfunc)smisk_Response___call__,                         /*tp_call*/
  0,                         /*tp_str*/
  0,                         /*tp_getattro*/
  0,                         /*tp_setattro*/
  0,                         /*tp_as_buffer*/
  Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE, /*tp_flags*/
  smisk_Response_DOC,          /*tp_doc*/
  0,                         /* tp_traverse */
  0,                         /* tp_clear */
  0,                         /* tp_richcompare */
  0,                         /* tp_weaklistoffset */
  0,                         /* tp_iter */
  0,                         /* tp_iternext */
  smisk_Response_methods,      /* tp_methods */
  smisk_Response_members,      /* tp_members */
  smisk_Response_getset,       /* tp_getset */
  0,                           /* tp_base */
  0,                           /* tp_dict */
  0,                           /* tp_descr_get */
  0,                           /* tp_descr_set */
  0,                           /* tp_dictoffset */
  (initproc)smisk_Response_init, /* tp_init */
  0,                           /* tp_alloc */
  smisk_Response_new,           /* tp_new */
  0                            /* tp_free */
};

int smisk_Response_register_types(PyObject *module) {
  log_trace("ENTER");
  if (PyType_Ready(&smisk_ResponseType) == 0)
    return PyModule_AddObject(module, "Response", (PyObject *)&smisk_ResponseType);
  return -1;
}
