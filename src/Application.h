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
#ifndef SMISK_APPLICATION_H
#define SMISK_APPLICATION_H
#include <Python.h>
#include "Request.h"
#include "Response.h"

typedef struct {
  PyObject_HEAD;
  
  // Public Python
  PyTypeObject*   requestClass;
  PyTypeObject*   responseClass;
  smisk_Request*  request;
  smisk_Response* response;
  
  // Internal
  int includeExceptionInfoInErrors;
} smisk_Application;

// Type setup
extern PyTypeObject smisk_ApplicationType;
int smisk_Application_register_types(void);

// Methods
int  smisk_Application_init    (smisk_Application* self, PyObject* args, PyObject* kwargs);
void smisk_Application_dealloc (smisk_Application* self);

PyObject* smisk_Application_run     (smisk_Application* self, PyObject* args);
PyObject* smisk_Application_service (smisk_Application* self, PyObject* args);
PyObject* smisk_Application_exit    (smisk_Application* self);

#endif
