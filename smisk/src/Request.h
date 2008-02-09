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
#ifndef SMISK_REQUEST_H
#define SMISK_REQUEST_H
#include <Python.h>
#include "Stream.h"
#include "URL.h"

//#include <fcgi_config.h>
#include <fcgiapp.h>

#define FCGI_REQUEST_STATE_NEVER_ACCEPTED 0
#define FCGI_REQUEST_STATE_ACCEPTED 1
#define FCGI_REQUEST_STATE_FINISHED 2

/* Size of buffer used to convert values and keys in envp */
#define FCGI_REQUEST_ENVP_BUF_SIZE 1024

typedef struct {
  PyObject_HEAD;
  
  // Public Python & C
  smisk_Stream  *input;
  smisk_Stream  *err;
  PyObject      *env; // PyDictObject (lazy)
  smisk_URL     *url; // PyDictObject (lazy)
  
  // Public C
  FCGX_ParamArray envp;
  
  // Don't touch my privates!
  char  *envp_buf;
  
} smisk_Request;

// Only C public
int smisk_Request_reset (smisk_Request* self);

// Type setup
extern PyTypeObject smisk_RequestType;
int smisk_Request_register_types(void);

// Methods
int smisk_Request_init(smisk_Request* self, PyObject* args, PyObject* kwargs);
void smisk_Request_dealloc(smisk_Request* self);

#endif
