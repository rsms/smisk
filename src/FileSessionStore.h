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
#ifndef SMISK_FILE_SESSION_STORE_H
#define SMISK_FILE_SESSION_STORE_H
#include "SessionStore.h"

typedef struct {
  smisk_SessionStore parent;
  
  // Public Python & C
  PyObject *file_prefix; // string
  
  // Private C
  long gc_tid;
  int gc_run;
  
} smisk_FileSessionStore;

extern PyTypeObject smisk_FileSessionStoreType;

int smisk_FileSessionStore_register_types (PyObject *module);

PyObject *smisk_FileSessionStore_new (PyTypeObject *type, PyObject *args, PyObject *kwds);
PyObject *smisk_FileSessionStore_refresh (smisk_FileSessionStore *self, PyObject *session_id);
PyObject *smisk_FileSessionStore_gc (smisk_FileSessionStore* self);

#endif
