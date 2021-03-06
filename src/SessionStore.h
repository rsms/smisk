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
#ifndef SMISK_SESSION_STORE_H
#define SMISK_SESSION_STORE_H

typedef struct {
  PyObject_HEAD;
  
  // Public Python
  int ttl; /// Lifetime in seconds
  PyObject *name; /// Name of session in cookie
  
} smisk_SessionStore;

extern PyTypeObject smisk_SessionStoreType;

int smisk_SessionStore_register_types (PyObject *module);

PyObject *smisk_SessionStore_new (PyTypeObject *type, PyObject *args, PyObject *kwds);
int       smisk_SessionStore_init (smisk_SessionStore* self, PyObject *args, PyObject *kwargs);
void      smisk_SessionStore_dealloc (smisk_SessionStore* self);

PyObject *smisk_SessionStore_read (smisk_SessionStore* self, PyObject *session_id);
PyObject *smisk_SessionStore_write (smisk_SessionStore* self, PyObject *args);
PyObject *smisk_SessionStore_refresh (smisk_SessionStore* self, PyObject *session_id);
PyObject *smisk_SessionStore_destroy (smisk_SessionStore* self, PyObject *session_id);

#endif
