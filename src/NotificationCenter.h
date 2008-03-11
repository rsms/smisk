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
#ifndef SMISK_NOTIFICATION_CENTER_H
#define SMISK_NOTIFICATION_CENTER_H
#include <Python.h>

typedef struct {
  PyObject_HEAD;
  PyObject* observers; // dict
} smisk_NotificationCenter;

// Type setup
extern PyTypeObject smisk_NotificationCenterType;
int smisk_NotificationCenter_register_types(PyObject *module);

// Class Methods
PyObject* smisk_NotificationCenter_default (PyObject* cls);

// Instance Methods
PyObject *smisk_NotificationCenter_new (PyTypeObject *type, PyObject *args, PyObject *kwds);
     int  smisk_NotificationCenter_init        (smisk_NotificationCenter* self, PyObject* args, PyObject* kwargs);
     void smisk_NotificationCenter_dealloc     (smisk_NotificationCenter* self);
PyObject* smisk_NotificationCenter_subscribe   (smisk_NotificationCenter* self, PyObject* args);
PyObject* smisk_NotificationCenter_unsubscribe (smisk_NotificationCenter* self, PyObject* args);
PyObject* smisk_NotificationCenter_post        (smisk_NotificationCenter* self, PyObject* args);

// Internal utilities
PyObject* smisk_NotificationCenter_postc (smisk_NotificationCenter* self, PyObject* args );

// Convenience macro
#define POST_NOTIFICATION1(n, arg1) \
  smisk_NotificationCenter_postc((smisk_NotificationCenter *)smisk_NotificationCenter_default(NULL), \
    PyTuple_Pack(2, n, arg1))

#endif
