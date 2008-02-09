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
#include "Response.h"
#include "Application.h"
#include <structmember.h>
#include <fastcgi.h>

/**************** internal functions *******************/


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


// Called by Application.run just after a successful accept() 
// and just before calling service().
int smisk_Response_reset (smisk_Response* self) {
  self->has_begun = 0;
  
  Py_XDECREF(self->headers);
  self->headers = PyList_New(0);
  if (self->headers == NULL) {
    DLog("self->headers == NULL");
    return -1;
  }
  
  return 0;
}


// Called by Application.run() after a successful call to service()
void smisk_Response_finish(smisk_Response* self) {
  //DLog("ENTER smisk_Response_finish");
  if(!self->has_begun) {
    smisk_Response_begin(self, NULL);
  }
}



/**************** instance methods *******************/

int smisk_Response_init(smisk_Response* self, PyObject* args, PyObject* kwargs) {
  DLog("ENTER smisk_Response_init");
  
  self->has_begun = 0;
  self->headers = NULL;
  self->app = NULL;
  
  if(smisk_Response_reset(self) == -1) {
    Py_DECREF(self);
    return -1;
  }
  
  // Construct a new Stream for out
  self->out = (smisk_Stream*)PyObject_Call((PyObject*)&smisk_StreamType, NULL, NULL);
  if (self->out == NULL) {
    DLog("self->out == NULL");
    Py_DECREF(self);
    return -1;
  }
  
  return 0;
}

void smisk_Response_dealloc(smisk_Response* self) {
  DLog("ENTER smisk_Response_dealloc");
  Py_XDECREF(self->out);
  Py_XDECREF(self->headers);
}


PyDoc_STRVAR(smisk_Response_sendfile_DOC,
  "Send a file to the client in a performance optimal way.\n"
  "\n"
  "If sendfile functionality is not available or not supported by the host "
  "server, this will fail silently. (Sorry for that!)\n"
  "\n"
  "Currently only lighttpd is supported through <tt>X-LIGHTTPD-send-file</tt> header.\n"
  "\n"
  "This method must be called before any body output has been sent.\n"
  "\n"
  "@param  filename If this is a relative path, it's relative to the host server root.\n"
  "@type   filename string\n"
  "@raises smisk.IOError if something i/o failed.\n"
  "@rtype  None");
PyObject* smisk_Response_sendfile(smisk_Response* self, PyObject* args) {
  int rc;
  PyObject* filename;
  
  // Did we get enough arguments?
  if(PyTuple_GET_SIZE(args) != 1) {
    return PyErr_Format(PyExc_TypeError, "sendfile takes exactly 1 argument");
  }
  
  // Save reference to first argument and type check it
  filename = PyTuple_GET_ITEM(args, 0);
  if(!PyString_Check(filename)) {
    return PyErr_Format(PyExc_TypeError, "first argument must be a string");
  }
  
  char *server = "-";
  (self->app && (server = FCGX_GetParam("SERVER_SOFTWARE", ((smisk_Application *)self->app)->request->envp)));
  
  if(strstr(server, "lighttpd/1.4")) {
    FCGX_PutStr("X-LIGHTTPD-send-file: ", 22, self->out->stream);
  }
  else if(strstr(server, "lighttpd/") || strstr(server, "apache/2")) {
    FCGX_PutStr("X-Sendfile: ", 12, self->out->stream);
  }
  else {
    return PyErr_Format(PyExc_EnvironmentError, "sendfile not supported by this server ('%s')", server);
  }
  
  FCGX_PutStr(PyString_AsString(filename), PyString_Size(filename), self->out->stream);
  rc = FCGX_PutStr("\r\n\r\n", 4, self->out->stream);
  self->has_begun = 1;
  
  // Check for errors
  if(rc == -1) {
    return PyErr_SET_FROM_ERRNO_OR_CUSTOM(smisk_IOError, "Failed to write on stream");
  }
  
  Py_RETURN_NONE;
}


PyDoc_STRVAR(smisk_Response_begin_DOC,
  "Begin response - send headers.\n"
  "\n"
  "Automatically called on before a buffer is flushed, when a\n"
  "service() call has ended or might be explicitly called inside service()."
  "\n"
  ":rtype: None");
PyObject* smisk_Response_begin(smisk_Response* self, PyObject* noargs) {
  //DLog("ENTER smisk_Response_begin");
  int rc;
  Py_ssize_t num_headers, i;
  
  // Headers?
  if(self->headers && PyList_Check(self->headers) && (num_headers = PyList_GET_SIZE(self->headers))) {
    // Iterate over headers
    PyObject* str;
    for(i=0;i<num_headers;i++) {
      str = PyList_GET_ITEM(self->headers, i);
      if(str && PyString_CheckExact(str)) {
        FCGX_PutStr(PyString_AS_STRING(str), PyString_GET_SIZE(str), self->out->stream);
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
  
  self->has_begun = 1;
  
  // Errors?
  if(rc == -1) {
    return PyErr_SET_FROM_ERRNO_OR_CUSTOM(smisk_IOError, "Failed to write on stream");
  }
  
  Py_RETURN_NONE;
}


PyDoc_STRVAR(smisk_Response_write_DOC,
  "Write data to the output buffer.\n"
  "\n"
  "When output buffer is full, begin() will be called, output buffer "
  "flushed and all following calls to write() will be the same as "
  "out.write() (\"unbuffered\").\n"
  "\n"
  ":param    string: Data.\n"
  ":type     string: string\n"
  ":raises   smisk.IOError: if something i/o failed.\n"
  ":rtype:   None");
PyObject* smisk_Response_write(smisk_Response* self, PyObject* str) {
  Py_ssize_t length;
  
  if(!str || !PyString_Check(str)) {
    return PyErr_Format(PyExc_TypeError, "first argument must be a string");
  }
  
  // TODO: make this method accept a length argument and use that instead if available
  length = PyString_GET_SIZE(str);
  if(!length) {
    // No data/Empty string
    Py_RETURN_NONE;
  }
  
  // Send HTTP headers
  if(!self->has_begun) {
    if(smisk_Response_begin(self, NULL) == NULL) {
      return NULL;
    }
  }
  
  // Write data
  if( smisk_Stream_perform_write(self->out, str, PyString_GET_SIZE(str)) == -1 ) {
    return NULL;
  }
  
  Py_RETURN_NONE;
}


PyDoc_STRVAR(smisk_Response_has_begun_DOC,
  "Check if output (http headers) has been sent to the client.\n"
  "\n"
  ":returns: True if begin() has been called and output has started.\n"
  ":rtype:   bool");
PyObject* smisk_Response_has_begun(smisk_Response* self, PyObject* str) {
  PyObject* b = self->has_begun ? Py_True : Py_False;
  Py_INCREF(b);
  return b;
}


/**************** type configuration *******************/

PyDoc_STRVAR(smisk_Response_DOC,
  "A FastCGI request\n"
  "\n"
  ":ivar out:     Output stream.\n"
  ":type out:     smisk.Stream\n"
  ":ivar headers: HTTP headers.\n"
  ":type headers: list");

// Methods
static PyMethodDef smisk_Response_methods[] =
{
  {"sendfile", (PyCFunction)smisk_Response_sendfile, METH_VARARGS, smisk_Response_sendfile_DOC},
  {"begin",    (PyCFunction)smisk_Response_begin,    METH_NOARGS,  smisk_Response_begin_DOC},
  {"write",    (PyCFunction)smisk_Response_write,    METH_O,       smisk_Response_write_DOC},
  {"has_begun",(PyCFunction)smisk_Response_has_begun, METH_NOARGS, smisk_Response_has_begun_DOC},
  {NULL}
};

// Properties (Members)
static struct PyMemberDef smisk_Response_members[] =
{
  {"out",          T_OBJECT_EX, offsetof(smisk_Response, out),          RO, NULL},
  {"headers",      T_OBJECT_EX, offsetof(smisk_Response, headers),      0,  NULL},
  {NULL}
};

// Type definition
PyTypeObject smisk_ResponseType = {
  PyObject_HEAD_INIT(&PyType_Type)
  0,                         /*ob_size*/
  "smisk.Response",             /*tp_name*/
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
  0,                         /*tp_call*/
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
  0,                         /* tp_getset */
  0,                           /* tp_base */
  0,                           /* tp_dict */
  0,                           /* tp_descr_get */
  0,                           /* tp_descr_set */
  0,                           /* tp_dictoffset */
  (initproc)smisk_Response_init, /* tp_init */
  0,                           /* tp_alloc */
  PyType_GenericNew,           /* tp_new */
  0                            /* tp_free */
};

extern int smisk_Response_register_types(void)
{
    return PyType_Ready(&smisk_ResponseType);
}
