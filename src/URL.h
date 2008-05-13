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
#ifndef SMISK_URL_H
#define SMISK_URL_H
#include <Python.h>

typedef struct {
  PyObject_HEAD;
  
  // Public Python & C
  PyObject* scheme;
  PyObject* user;
  PyObject* password;
  PyObject* host;
  int port;
  PyObject* path;
  PyObject* query;
  PyObject* fragment;
  
} smisk_URL;

// C API only
size_t smisk_url_decode (char *str, size_t len); // returns (new) length of str
char *smisk_url_encode (const char *s, int full); // returns a newly allocated string

// Type setup
extern PyTypeObject smisk_URLType;
int smisk_URL_register_types (PyObject *module);

// Methods
PyObject *smisk_URL_new (PyTypeObject *type, PyObject *args, PyObject *kwds);
int smisk_URL_init (smisk_URL* self, PyObject* args, PyObject* kwargs);
void smisk_URL_dealloc (smisk_URL* self);

#endif
