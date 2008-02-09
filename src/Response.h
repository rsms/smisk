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
#ifndef SMISK_RESPONSE_H
#define SMISK_RESPONSE_H
#include <Python.h>
#include "Stream.h"

//#include <fcgi_config.h>
#include <fcgiapp.h>

typedef struct {
  PyObject_HEAD;
  
  // Public Python & C
  smisk_Stream* out;
  PyObject*    headers; // list
  PyObject*    status;  // string
  
  // Private
  int has_begun;
  PyObject *app; // smisk_Application
  
} smisk_Response;

// Internal functions
int smisk_Response_reset (smisk_Response* self); // returns -1 on error
void smisk_Response_finish (smisk_Response* self);

// Type setup
extern PyTypeObject smisk_ResponseType;
int smisk_Response_register_types (void);

// Methods
int smisk_Response_init (smisk_Response* self, PyObject* args, PyObject* kwargs);
void smisk_Response_dealloc (smisk_Response* self);
PyObject* smisk_Response_begin (smisk_Response* self, PyObject* noargs);

#endif
