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
#ifndef PY_FCGI_REQUEST_H
#define PY_FCGI_REQUEST_H
#include "Stream.h"
#include <Python.h>

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
	fcgi_Stream*  input;
	fcgi_Stream*  out;
	fcgi_Stream*  err;
	PyDictObject* params;
	
	// Public C
	FCGX_Request       req;
	
	// Don't touch my privates!
	int    state;
	char*  envp_buf;
	
} fcgi_Request;

// Type setup
extern PyTypeObject fcgi_RequestType;
int fcgi_Request_register_types(void);

// Methods
int fcgi_Request_init(fcgi_Request* self, PyObject* args, PyObject* kwargs);
void fcgi_Request_dealloc(fcgi_Request* self);

PyObject* fcgi_Request_accept(fcgi_Request* self);
PyObject* fcgi_Request_commit(fcgi_Request* self);

#endif
