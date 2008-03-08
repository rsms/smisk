/*
Copyright (c) 2007 Rasmus Andersson

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
#include "Stream.h"
#include <structmember.h>


#pragma mark Initialization & deallocation


static PyObject * smisk_Stream_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {
  log_debug("ENTER smisk_Stream_new");
  smisk_Stream *self;
  
  self = (smisk_Stream *)type->tp_alloc(type, 0);
  if (self != NULL) {
    self->stream = NULL;
  }
  
  return (PyObject *)self;
}


int smisk_Stream_init(smisk_Stream* self, PyObject* args, PyObject* kwargs) {
  return 0;
}


void smisk_Stream_dealloc(smisk_Stream* self) {
  log_debug("ENTER smisk_Stream_dealloc");
}


#pragma mark -
#pragma mark Methods


PyDoc_STRVAR(smisk_Stream_readline_DOC,
  "Read one entire line from the file. "
  "A trailing newline character is kept in the string (but may be absent when "
  "a file ends with an incomplete line) If the size argument is present and "
  "non-negative, it is a maximum byte count (including the trailing newline) "
  "and an incomplete line may be returned. An empty string is returned only "
  "when EOF is encountered immediately\n"
  "\n"
  ":type   length: int\n"
  ":param  length: read up to length bytes.\n"
  ":rtype: string\n"
  ":returns: the line read or None if EOF");
PyObject* smisk_Stream_readline(smisk_Stream* self, PyObject* args) {
  PyObject *str, *arg1;
  Py_ssize_t length;
  
  // Get length
  if (args && PyTuple_GET_SIZE(args) > 0) {
    if( (arg1 = PyTuple_GET_ITEM(args, 1)) == NULL ) {
      length = SMISK_STREAM_READLINE_LENGTH;
    }
    else if(!PyInt_Check(arg1)) {
      PyErr_Format(PyExc_TypeError, "length argument must be an integer");
      return NULL;
    }
    else {
      length = PyInt_AS_LONG(arg1);
    }
  }
  else {
    length = SMISK_STREAM_READLINE_LENGTH;
  }
  
  // Init string
  if((str = PyString_FromStringAndSize(NULL, length)) == NULL) {
    return NULL;
  }
  
  // Setup vars for the acctual read loop
  int c;
  Py_ssize_t n;
  char *po, *p;
  
  po = PyString_AS_STRING(str);
  p = po;
  n = length;
  
  // Read loop
  // We are doing our own, optimized readline proc here
  while (n > 0) {
    c = FCGX_GetChar(self->stream);
    
    if(c == EOF) {
      if(p == po) {
        // First byte was EOF
        Py_DECREF(str);
        Py_RETURN_NONE;
      }
      break;
    }
    
    *p++ = (char) c;
    n--;
    
    if(c == '\n')
      break;
  }
  
  length -= n;
  
  // Resize string (Almost all cases need this so no check before)
  if(_PyString_Resize(&str, length) == -1) {
    log_error("_PyString_Resize(%p, %ld) == -1", str, (long)length);
    return NULL;
  }
  
  return str;
}


PyDoc_STRVAR(smisk_Stream_read_DOC,
  "Read at most size bytes from the file (less if the read hits EOF before "
  "obtaining size bytes). If the size  argument is negative or omitted, "
  "read all data until EOF is reached.\n"
  "\n"
  ":type   length: int\n"
  ":param  length: read up to length bytes. If not specified or negative, read until EOF.\n"
  ":rtype: string");
PyObject* smisk_Stream_read(smisk_Stream* self, PyObject* args) {
  //log_debug("ENTER smisk_Stream_read");
  PyObject *str, *arg1;
  Py_ssize_t length;
  int rc;
  
  // Get length
  if (PyTuple_GET_SIZE(args) > 0) {
    if( (arg1 = PyTuple_GET_ITEM(args, 1)) == NULL ) { // None
      length = -1;
    }
    else if(!PyInt_Check(arg1)) {
      PyErr_Format(PyExc_TypeError, "length argument must be an integer");
      return NULL;
    }
    else {
      length = PyInt_AS_LONG(arg1);
    }
  }
  else {
    length = -1;
  }
  
  // Read n bytes
  if(length > 0)  {
    // Init string
    if((str = PyString_FromStringAndSize(NULL, length)) == NULL)
      return NULL;
    
    rc = FCGX_GetStr(PyString_AS_STRING(str), length, self->stream);
    // rc is now bytes read (will never be less than 0)
    
    // Size down the string if needed
    if(rc < length && _PyString_Resize(&str, (Py_ssize_t)rc) != 0) {
      Py_DECREF(str);
      log_error("_PyString_Resize(%p, %d) == -1", str, rc);
      return NULL;
    }
  }
  // Zero is Zero!
  else if(length == 0) {
    if((str = PyString_FromStringAndSize("", 0)) == NULL) {
      return NULL;
    }
  }
  // Read all
  else {
    ssize_t bufchunksize, bufsize, buflength;
    char *strdat;
    
    // init vars
    bufchunksize = bufsize = SMISK_STREAM_READ_CHUNKSIZE;
    buflength = 0;
    rc = 0;
    
    // Create string
    if((str = PyString_FromStringAndSize(NULL, bufsize)) == NULL) {
      return NULL;
    }
    
    // Start reading
    while(1) {
      strdat = PyString_AS_STRING(str)+rc;
      rc = FCGX_GetStr(strdat, bufchunksize, self->stream);
      // note: FCGX_GetStr does not return error indication. Lowest return value is 0.
      
      // Increase length
      buflength += rc;
      
      // Check EOF
      if(rc < bufchunksize)
        break;
      
      // Need resize?
      if(bufsize < buflength+bufchunksize) {
        bufsize *= 2;
        if(_PyString_Resize(&str, bufsize) == -1) {
          log_error("_PyString_Resize(%p, %ld) == -1", str, (long)bufsize);
          return NULL;
        }
      }
    }
    
    // Size down the string to the correct length
    if(_PyString_Resize(&str, buflength) == -1) {
      log_debug("_PyString_Resize(%p, %ld) == -1", str, buflength);
      return NULL;
    }
  }
  
  return str;
}


PyDoc_STRVAR(smisk_Stream_write_byte_DOC,
  "Write a byte to the stream.\n"
  "\n"
  ":param  b: The byte to write\n"
  ":type   b: int\n"
  ":rtype: None\n"
  ":raises smisk.IOError: if the byte could not be written");
PyObject* smisk_Stream_write_byte(smisk_Stream* self, PyObject* ch) {
  if(!ch || !PyInt_Check(ch)) {
    PyErr_Format(PyExc_TypeError, "first argument must be an integer");
    return NULL;
  }
  
  if(FCGX_PutChar((int)PyInt_AS_LONG(ch), self->stream) == -1) {
    return PyErr_SET_FROM_ERRNO_OR_CUSTOM(smisk_IOError, "Failed to write on stream");
  }
  
  Py_RETURN_NONE;
}


PyDoc_STRVAR(smisk_Stream_write_DOC,
  "Write data to the stream.\n"
  "\n"
  "It is guaranteed to write all bytes. If any byte fails to be "
  "written, a smisk.IOError is raised.\n"
  "\n"
  ":type   str:    string\n"
  ":param  str:    a string\n"
  ":type   length: int\n"
  ":param  length: write length bytes from str (optional)\n"
  ":rtype: None\n"
  ":raises smisk.IOError:");
PyObject* smisk_Stream_write(smisk_Stream* self, PyObject* args) {
  PyObject* str;
  Py_ssize_t length;
  int argc;
  
  argc = PyTuple_GET_SIZE(args);
  
  // Did we get enough arguments?
  if(argc == 0) {
    return PyErr_Format(PyExc_TypeError, "write takes at least 1 argument (0 given)");
  }
  
  // Save reference to first argument and type check it
  str = PyTuple_GET_ITEM(args, 0);
  if(!PyString_Check(str)) {
    return PyErr_Format(PyExc_TypeError, "First argument must be a string");
  }
  
  // Figure out length
  if (argc > 1) {
    PyObject* arg1 = PyTuple_GET_ITEM(args, 1);
    if(!PyInt_Check(arg1)) {
      return PyErr_Format(PyExc_TypeError, "Second argument must be an integer");
    }
    length = PyInt_AS_LONG(arg1);
  }
  else {
    length = PyString_GET_SIZE(str);
  }
  
  // Write to stream
  if( length && smisk_Stream_perform_write(self, str, length) == -1 ) {
    return NULL;
  }
  
  Py_RETURN_NONE;
}


int smisk_Stream_perform_write(smisk_Stream* self, PyObject* str, Py_ssize_t length) {
  if( FCGX_PutStr(PyString_AS_STRING(str), length, self->stream) == -1 ) {
    PyErr_SET_FROM_ERRNO_OR_CUSTOM(smisk_IOError, "Failed to write on stream");
    return -1;
  }
  return 0;
}


PyDoc_STRVAR(smisk_Stream_flush_DOC,
  "Flush the internal buffer. This reduces performance and is "
  "only needed for \"server-push\" applications. The parent request object "
  "always implicitly flushes all it's streams upon finishing the request.\n"
  "\n"
  ":rtype: None");
PyObject* smisk_Stream_flush(smisk_Stream* self) {
  if(FCGX_FFlush(self->stream) == -1) {
    return PyErr_SET_FROM_ERRNO_OR_CUSTOM(smisk_IOError, "Failed to flush stream");
  }
  Py_RETURN_NONE;
}


PyDoc_STRVAR(smisk_Stream_close_DOC,
  "Close the stream. You should never need to close a FastCGI "
  "stream, as it's safely handled by the internals of the parent request "
  "object.\n"
  "\n"
  ":rtype: None");
PyObject* smisk_Stream_close(smisk_Stream* self) {
  if(FCGX_FClose(self->stream) == -1) {
    return PyErr_SET_FROM_ERRNO_OR_CUSTOM(smisk_IOError, "Failed to close stream");
  }
  Py_RETURN_NONE;
}


#pragma mark -
#pragma mark Iteration


PyObject* smisk_Stream_iter(smisk_Stream *self) {
  Py_INCREF(self);
  return (PyObject*)self;
}

PyObject* smisk_Stream_iternext(smisk_Stream *self) {
  PyObject* str = smisk_Stream_readline(self, NULL);
  if(PyString_GET_SIZE(str) == 0) {
    // End iteration
    // XXX I think we need to raise a EndIteration exception here, don't we?
    Py_DECREF(str);
    return NULL;
  }
  return str;
}


#pragma mark -
#pragma mark Type construction

PyDoc_STRVAR(smisk_Stream_DOC,
  "FastCGI input/output stream");

static PyMethodDef smisk_Stream_methods[] = {
  {"close", (PyCFunction)smisk_Stream_close,            METH_NOARGS,  smisk_Stream_close_DOC},
  {"flush", (PyCFunction)smisk_Stream_flush,            METH_NOARGS,  smisk_Stream_flush_DOC},
  {"read", (PyCFunction)smisk_Stream_read,              METH_VARARGS, smisk_Stream_read_DOC},
  {"readline", (PyCFunction)smisk_Stream_readline,      METH_VARARGS, smisk_Stream_readline_DOC},
  {"write", (PyCFunction)smisk_Stream_write,            METH_VARARGS, smisk_Stream_write_DOC},
  {"write_byte", (PyCFunction)smisk_Stream_write_byte,  METH_O,       smisk_Stream_write_byte_DOC},
  {NULL}
};

static struct PyMemberDef smisk_Stream_members[] = {
  {NULL}
};

PyTypeObject smisk_StreamType = {
  PyObject_HEAD_INIT(NULL)
  0,                         /*ob_size*/
  "smisk.core.Stream",             /*tp_name*/
  sizeof(smisk_Stream),       /*tp_basicsize*/
  0,                         /*tp_itemsize*/
  (destructor)smisk_Stream_dealloc,        /* tp_dealloc */
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
  Py_TPFLAGS_DEFAULT,        /*tp_flags*/
  smisk_Stream_DOC,           /*tp_doc*/
  0,                                              /* tp_traverse */
  0,                                              /* tp_clear */
  0,                                              /* tp_richcompare */
  0,                                              /* tp_weaklistoffset */
  (getiterfunc)smisk_Stream_iter,                  /* tp_iter */
  (iternextfunc)smisk_Stream_iternext,             /* tp_iternext */
  smisk_Stream_methods,                      /* tp_methods */
  smisk_Stream_members,                      /* tp_members */
  0,                                              /* tp_getset */
  0,                                              /* tp_base */
  0,                                              /* tp_dict */
  0,                                              /* tp_descr_get */
  0,                                              /* tp_descr_set */
  0,                                              /* tp_dictoffset */
  (initproc)smisk_Stream_init,               /* tp_init */
  0,                                              /* tp_alloc */
  smisk_Stream_new,                              /* tp_new */
  0                                               /* tp_free */
};

int smisk_Stream_register_types(PyObject *module) {
  if(PyType_Ready(&smisk_StreamType) == 0) {
    return PyModule_AddObject(module, "Stream", (PyObject *)&smisk_StreamType);
  }
  return -1;
}
