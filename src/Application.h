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
#ifndef SMISK_APPLICATION_H
#define SMISK_APPLICATION_H
#include <Python.h>
#include "Request.h"
#include "Response.h"

typedef struct {
  PyObject_HEAD;
  
  // Public Python
  PyTypeObject   *request_class;
  PyTypeObject   *response_class;
  smisk_Request  *request;
  smisk_Response *response;
  
  PyTypeObject   *sessions_class;
  PyObject       *sessions; // lazy Session store
  
  PyObject       *show_traceback; // bool
  
} smisk_Application;

// Current instance (NULL if none)
smisk_Application *smisk_Application_current;

// class Application (the Application type object)
PyTypeObject smisk_ApplicationType;

// Set error if smisk_Application_current is NULL and return -1. Returns 0 when app is available.
int smisk_require_app (void);

// Set Application.current to app. Returns 0 on success, -1 on failure.
int smisk_Application_set_current (PyObject *app);

// Type setup
int smisk_Application_register_types (PyObject *module);

// Methods
PyObject *smisk_Application_new (PyTypeObject *type, PyObject *args, PyObject *kwds);
int  smisk_Application_init    (smisk_Application* self, PyObject *args, PyObject *kwargs);
void smisk_Application_dealloc (smisk_Application* self);

PyObject *smisk_Application_run     (smisk_Application* self);
PyObject *smisk_Application_service (smisk_Application* self, PyObject *args);
PyObject *smisk_Application_exit    (smisk_Application* self);

PyObject *smisk_Application_get_sessions (smisk_Application* self);

// Get/setter for Application.current


#endif
