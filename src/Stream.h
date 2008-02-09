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
#ifndef PY_FCGI_STREAM_H
#define PY_FCGI_STREAM_H
#include <Python.h>
#include <fcgiapp.h>

typedef struct {
	PyObject_HEAD
	
	FCGX_Stream* stream;
	char*        readbuf;
	Py_ssize_t   readbuf_size;
	
} fcgi_Stream;

// Type setup
extern PyTypeObject fcgi_StreamType;
int fcgi_Stream_register_types(void);

// Methods
int fcgi_Stream_init(fcgi_Stream* self, PyObject* args, PyObject* kwargs);
void fcgi_Stream_dealloc(fcgi_Stream* self);

#endif
