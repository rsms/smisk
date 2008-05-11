/*
Copyright (c) 2007-2008, Rasmus Andersson

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
#ifndef SMISK_STREAM_H
#define SMISK_STREAM_H
#include <Python.h>
#include <fcgiapp.h>

typedef struct {
  PyObject_HEAD;
  
  FCGX_Stream* stream;
  
} smisk_Stream;

// Type setup
extern PyTypeObject smisk_StreamType;
int smisk_Stream_register_types (PyObject *module);

// Methods
PyObject *smisk_Stream_new (PyTypeObject *type, PyObject *args, PyObject *kwds);
int smisk_Stream_init (smisk_Stream *self, PyObject *args, PyObject *kwargs);
void smisk_Stream_dealloc (smisk_Stream *self);

// Internal methods
int smisk_Stream_perform_write (smisk_Stream *self, PyObject *str, Py_ssize_t length); // returns -1 on error

#endif
