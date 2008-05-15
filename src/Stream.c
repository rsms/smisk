/*
Copyright (c) 2007-2008 Rasmus Andersson and contributors

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


#pragma mark Private C


// DRY helper for methods accepting an optional Py_ssize_t arg
// Return 1 (true) on success, 0 (false) on failure
// If len is NULL, length will get the value of default
static int _get_opt_ssize_arg(Py_ssize_t *length, PyObject *args, Py_ssize_t pos, Py_ssize_t def) {
  PyObject *len;
  if (args && PyTuple_GET_SIZE(args) > pos) {
    if( (len = PyTuple_GET_ITEM(args, pos)) == NULL )
      return 0;
    
    if(!PyInt_Check(len)) {
      PyErr_Format(PyExc_TypeError, "first argument must be an integer");
      return 0;
    }
    else {
      *length = PyInt_AS_LONG(len);
    }
  }
  else {
    *length = SMISK_STREAM_READLINE_LENGTH;
  }
  return 1;
}


#pragma mark -
#pragma mark Public C


int smisk_Stream_perform_write(smisk_Stream* self, PyObject *str, Py_ssize_t length) {
  if( FCGX_PutStr(PyString_AS_STRING(str), length, self->stream) == -1 ) {
    PyErr_SET_FROM_ERRNO;
    return -1;
  }
  return 0;
}


#pragma mark -
#pragma mark Initialization & deallocation


PyObject * smisk_Stream_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {
  log_trace("ENTER");
  smisk_Stream *self;
  
  self = (smisk_Stream *)type->tp_alloc(type, 0);
  if (self != NULL) {
    self->stream = NULL;
  }
  
  return (PyObject *)self;
}


int smisk_Stream_init(smisk_Stream* self, PyObject *args, PyObject *kwargs) {
  log_trace("ENTER");
  return 0;
}


void smisk_Stream_dealloc(smisk_Stream* self) {
  log_trace("ENTER");
  self->ob_type->tp_free((PyObject*)self);
}


#pragma mark -
#pragma mark Methods


PyDoc_STRVAR(smisk_Stream_readline_DOC,
  "Read one entire line from the file.\n"
  "\n"
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
PyObject *smisk_Stream_readline(smisk_Stream* self, PyObject *args) {
  log_trace("ENTER");
  PyObject *str;
  Py_ssize_t length;
  
  if(!_get_opt_ssize_arg(&length, args, 0, SMISK_STREAM_READLINE_LENGTH))
    return NULL;
  
  // Init string
  if((str = PyString_FromStringAndSize(NULL, length)) == NULL)
    return NULL;
  
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


PyDoc_STRVAR(smisk_Stream_readlines_DOC,
  "Read until EOF using readline() and return a list containing the lines thus read.\n"
  "\n"
  "If the optional sizehint argument is present, instead of reading up to EOF, whole lines totalling approximately sizehint bytes (possibly after rounding up to an internal buffer size) are read.\n"
  "\n"
  ":type   length: int\n"
  ":param  length: sizehint\n"
  ":rtype: list");
PyObject *smisk_Stream_readlines(smisk_Stream* self, PyObject *args) {
  log_trace("ENTER");
  Py_ssize_t sizehint, linecount;
  PyObject *lines, *line, *readline_args;
  
  if (!_get_opt_ssize_arg(&sizehint, args, 0, -1))
    return NULL;
  
  // We hold the reference until we return
  lines = PyList_New(sizehint);
  
  // Euhm, we were asked to read nothing -- let's read nothing then.
  if (sizehint == 0)
    return lines;
  
  // Temporary args list
  readline_args = PyList_New(0);
  
  for (linecount = 0; linecount < sizehint; linecount++) {
    // Discussion:  Here, we are calling readline directly. If the user
    //              overrides Stream.readline the original implementation will
    //              still be called. However, calling this using "message 
    //              passing" is considerably slower. One way of getting the
    //              best of both worlds might be to somehow "detect" that
    //              readline has been overridden and if so, use an alternative
    //              loop which uses "message passing".
    //             
    if ((line = smisk_Stream_readline(self, readline_args)) == NULL) {
      Py_DECREF(readline_args);
      return NULL;
    }
    // Assign to list
    PyList_SET_ITEM(lines, linecount, line);
  }
  
  // We do not need to run smisk_Stream_readline anymore
  Py_DECREF(readline_args);
  
  // Slice the list to get rid of stale NULLs
  if (linecount < sizehint) {
    PyObject *old_lines = lines;
    lines = PyList_GetSlice(lines, 0, linecount-1);
    Py_DECREF(old_lines);
    // At this point, lines may be NULL if PyList_GetSlice failed, but we
    // return lines now, so things are handled just fine. But be careful if
    // adding code below.
  }
  
  return lines;
}


PyDoc_STRVAR(smisk_Stream_read_DOC,
  "Read at most size bytes from the file (less if the read hits EOF before "
  "obtaining size bytes). If the size  argument is negative or omitted, "
  "read all data until EOF is reached.\n"
  "\n"
  ":type   length: int\n"
  ":param  length: read up to length bytes. If not specified or negative, read until EOF.\n"
  ":rtype: string");
PyObject *smisk_Stream_read(smisk_Stream* self, PyObject *args) {
  log_trace("ENTER");
  PyObject *str;
  Py_ssize_t length;
  int rc;
  
  if(!_get_opt_ssize_arg(&length, args, 0, -1))
    return NULL;
  
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
    if((str = PyString_FromStringAndSize("", 0)) == NULL)
      return NULL;
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
    if((str = PyString_FromStringAndSize(NULL, bufsize)) == NULL)
      return NULL;
    
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
PyObject *smisk_Stream_write_byte(smisk_Stream* self, PyObject *ch) {
  log_trace("ENTER");
  if(!ch || !PyInt_Check(ch)) {
    PyErr_Format(PyExc_TypeError, "first argument must be an integer");
    return NULL;
  }
  
  if(FCGX_PutChar((int)PyInt_AS_LONG(ch), self->stream) == -1)
    return PyErr_SET_FROM_ERRNO;
  
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
PyObject *smisk_Stream_write(smisk_Stream* self, PyObject *args) {
  log_trace("ENTER");
  PyObject *str;
  Py_ssize_t length, argc;
  
  argc = PyTuple_GET_SIZE(args);
  
  // Did we get enough arguments?
  if(argc == 0)
    return PyErr_Format(PyExc_TypeError, "write takes at least 1 argument (0 given)");
  
  // Save reference to first argument and type check it
  str = PyTuple_GET_ITEM(args, 0);
  if(!PyString_Check(str))
    return PyErr_Format(PyExc_TypeError, "first argument must be a string");
  
  // Figure out length
  if (argc > 1) {
    PyObject *arg1 = PyTuple_GET_ITEM(args, 1);
    if(!PyInt_Check(arg1))
      return PyErr_Format(PyExc_TypeError, "second argument must be an integer");
    length = PyInt_AS_LONG(arg1);
  }
  else {
    length = PyString_GET_SIZE(str);
  }
  
  // Write to stream
  if( length && smisk_Stream_perform_write(self, str, length) != 0 )
    return NULL;
  
  Py_RETURN_NONE;
}


// If first_write_cb is specified, it's called before first line is written.
// If first_write_cb returns other than 0, an error has occured and this function returns NULL.
PyObject *smisk_Stream_perform_writelines(smisk_Stream *self,
                                          PyObject *sequence, 
                                          smisk_Stream_perform_writelines_cb *first_write_cb,
                                          void *cb_user_data)
{
  // no trace here
  PyObject *iterator, *string;
  Py_ssize_t string_length;
  
  if ((iterator = PyObject_GetIter(sequence)) == NULL)
    return NULL;
  
  while ( (string = PyIter_Next(iterator)) ) {
    if(!PyString_Check(string)) {
      PyErr_Format(PyExc_TypeError, "iteration on sequence returned non-string object");
      Py_DECREF(string);
      break;
    }
    
    // We save length, so we can skip calling smisk_Stream_perform_write at all if
    // the string is empty.
    string_length = PyString_GET_SIZE(string);
    if( string_length ) {
      if (first_write_cb && first_write_cb(cb_user_data) != 0)
        return NULL;
      if (smisk_Stream_perform_write(self, string, string_length) != 0)
        return NULL;
    }
    
    Py_DECREF(string);
  }
  
  Py_DECREF(iterator);
  
  if (PyErr_Occurred())
    return NULL;
  
  Py_RETURN_NONE;
}


PyDoc_STRVAR(smisk_Stream_writelines_DOC,
  "Write a sequence of strings to the stream.\n"
  "\n"
  "The sequence can be any iterable object producing strings, typically a ''list'' of strings. There is no return value. (The name is intended to match readlines(); writelines() and alike does not add line separators.)\n"
  "\n"
  ":type   sequence: list\n"
  ":param  sequence: A sequence of strings\n"
  ":rtype: None\n"
  ":raises IOError:");
PyObject *smisk_Stream_writelines(smisk_Stream* self, PyObject *sequence) {
  log_trace("ENTER");
  return smisk_Stream_perform_writelines(self, sequence, NULL, NULL);
}


PyDoc_STRVAR(smisk_Stream_flush_DOC,
  "Flush the internal buffer. This reduces performance and is "
  "only needed for \"server-push\" applications. The parent request object "
  "always implicitly flushes all it's streams upon finishing the request.\n"
  "\n"
  ":rtype: None");
PyObject *smisk_Stream_flush(smisk_Stream* self) {
  log_trace("ENTER");
  if(FCGX_FFlush(self->stream) == -1)
    return PyErr_SET_FROM_ERRNO;
  Py_RETURN_NONE;
}


PyDoc_STRVAR(smisk_Stream_close_DOC,
  "Close the stream. You should never need to close a FastCGI "
  "stream, as it's safely handled by the internals of the parent request "
  "object.\n"
  "\n"
  ":rtype: None");
PyObject *smisk_Stream_close(smisk_Stream* self) {
  log_trace("ENTER");
  if(FCGX_FClose(self->stream) == -1)
    return PyErr_SET_FROM_ERRNO;
  Py_RETURN_NONE;
}


#pragma mark -
#pragma mark Iteration


PyObject *smisk_Stream___iter__(smisk_Stream *self) {
  log_trace("ENTER");
  return Py_INCREF(self), (PyObject*)self;
}

PyObject *smisk_Stream___iternext__(smisk_Stream *self) {
  log_trace("ENTER");
  // Conforms to PEP 234 <http://www.python.org/dev/peps/pep-0234/>
  PyObject *str = smisk_Stream_readline(self, NULL);
  if (PyString_GET_SIZE(str) == 0) {
    Py_DECREF(str);
    return NULL; // End iteration
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
  {"readlines", (PyCFunction)smisk_Stream_readlines,    METH_VARARGS, smisk_Stream_readlines_DOC},
  {"write", (PyCFunction)smisk_Stream_write,            METH_VARARGS, smisk_Stream_write_DOC},
  {"writelines", (PyCFunction)smisk_Stream_writelines,  METH_O,       smisk_Stream_writelines_DOC},
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
  (getiterfunc)smisk_Stream___iter__,       /* tp_iter */
  (iternextfunc)smisk_Stream___iternext__,  /* tp_iternext */
  smisk_Stream_methods,                     /* tp_methods */
  smisk_Stream_members,                     /* tp_members */
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
  log_trace("ENTER");
  if(PyType_Ready(&smisk_StreamType) == 0)
    return PyModule_AddObject(module, "Stream", (PyObject *)&smisk_StreamType);
  return -1;
}
