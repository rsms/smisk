/*
Copyright (c) 2007 Rasmus Andersson

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
#include "module.h"
#include "Stream.h"
#include <structmember.h>

#define READALL_CHUNKSIZE 64
#define READLINE_LENGTH 8192

int fcgi_Stream_init(fcgi_Stream* self, PyObject* args, PyObject* kwargs)
{
	//DLog("ENTER fcgi_Stream_init");
	self->stream = NULL;
	self->readbuf = NULL;
	self->readbuf_size = 0;
	//PyErr_SetString(PyExc_Exception, "Can not be instantiated");
	return 0;
}

void fcgi_Stream_dealloc(fcgi_Stream* self)
{
}


PyDoc_STRVAR(fcgi_Stream_readline_DOC,
	"Read one entire line from the file. "
	"A trailing newline character is kept in the string (but may be absent when "
	"a file ends with an incomplete line) If the size argument is present and "
	"non-negative, it is a maximum byte count (including the trailing newline) "
	"and an incomplete line may be returned. An empty string is returned only "
	"when EOF is encountered immediately\n"
	"\n"
	":type   length: int\n"
	":param  length: read up to length bytes.\n"
	":rtype: string\n"
	":returns: the line read or None if EOF");
PyObject* fcgi_Stream_readline(fcgi_Stream* self, PyObject* args)
{
	PyObject* str;
	Py_ssize_t length;
	
	// Get length
	if (args && PyTuple_GET_SIZE(args) > 0)
	{
		PyObject* arg1 = PyTuple_GET_ITEM(args, 1);
		if(arg1 == NULL) {
			// None
			length = READLINE_LENGTH;
		}
		else if(!PyInt_Check(arg1)) {
			PyErr_SetString(PyExc_TypeError, "length argument must be an integer");
			return NULL;
		}
		else {
			length = PyInt_AS_LONG(arg1);
		}
	}
	else {
		length = READLINE_LENGTH;
	}
	
	// Init string
	if((str = PyString_FromStringAndSize(NULL, length)) == NULL)
		return NULL;
	
	// Setup vars for the acctual read loop
	int c;
	Py_ssize_t n;
	char *po, *p;
	
	po = PyString_AS_STRING(str);
	p = po;
	n = length;
	
	THREADED_START;
	// Read loop
	while (n > 0)
	{
		c = FCGX_GetChar(self->stream);
		
		if(c == EOF)
		{
			if(p == po)
			{
				// If first byte was EOF
				THREADED_END;
				Py_DECREF(str);
				Py_RETURN_NONE;
			}
		
			break;
		}
		
		*p++ = (char) c;
		n--;
		
		if(c == '\n')
			break;
	}
	
	THREADED_END;
	length -= n;
	
	// Resize string (Almost all cases need this so no check before)
	if(_PyString_Resize(&str, length) == -1) {
		DLog("ERROR _PyString_Resize(0x%x, %ld) == -1", (unsigned int)str, length);
		return NULL;
	}
	
	Py_INCREF(str);
	return str;
}


PyDoc_STRVAR(fcgi_Stream_read_DOC,
	"Read at most size bytes from the file (less if the read hits EOF before "
	"obtaining size bytes). If the size  argument is negative or omitted, "
	"read all data until EOF is reached.\n"
	"\n"
	":type   length: int\n"
	":param  length: read up to length bytes. If not specified or negative, read until EOF.\n"
	":rtype: string");
PyObject* fcgi_Stream_read(fcgi_Stream* self, PyObject* args)
{
	//DLog("ENTER fcgi_Stream_read");
	PyObject* str;
	Py_ssize_t length;
	int rc;
	
	// Get length
	if (PyTuple_GET_SIZE(args) > 0)
	{
		PyObject* arg1 = PyTuple_GET_ITEM(args, 1);
		if(arg1 == NULL) // None
		{
			length = -1;
		}
		else if(!PyInt_Check(arg1))
		{
			PyErr_SetString(PyExc_TypeError, "length argument must be an integer");
			return NULL;
		}
		else
		{
			length = PyInt_AS_LONG(arg1);
		}
	}
	else {
		length = -1;
	}
	
	// Read n bytes
	if(length > 0)
	{
		// Init string
		if((str = PyString_FromStringAndSize(NULL, length)) == NULL)
			return NULL;
		
		THREADED(rc = FCGX_GetStr(PyString_AS_STRING(str), length, self->stream));
		// rc is now bytes read
		
		// Size down the string if needed
		if(rc < length && _PyString_Resize(&str, (Py_ssize_t)rc) == -1) {
			DLog("ERROR _PyString_Resize(0x%x, %d) == -1", (unsigned int)str, rc);
			return NULL;
		}
	}
	// Zero is Zero!
	else if(length == 0)
	{
		if((str = PyString_FromStringAndSize("", 0)) == NULL)
			return NULL;
	}
	// Read all
	else
	{
		ssize_t bufchunksize, bufsize, buflength;
		char *strdat;
		
		// init vars
		bufchunksize = bufsize = READALL_CHUNKSIZE;
		buflength = 0;
		rc = 0;
		
		// Create string
		if((str = PyString_FromStringAndSize(NULL, bufsize)) == NULL)
			return NULL;
		
		// Start reading
		THREADED_START;
		while(1)
		{
			strdat = PyString_AS_STRING(str)+rc;
			rc = FCGX_GetStr(strdat, bufchunksize, self->stream);
			
			// Increase length
			buflength += rc;
			
			// Check EOF
			if(rc < bufchunksize)
				break;
			
			// Need resize?
			if(bufsize < buflength+bufchunksize)
			{
				bufsize *= 2;
				if(_PyString_Resize(&str, bufsize) == -1) {
					DLog("ERROR _PyString_Resize(0x%x, %ld) == -1", (unsigned int)str, bufsize);
					THREADED_END;
					return NULL;
				}
			}
		}
		THREADED_END;
		
		// Size down the string to the correct length
		if(_PyString_Resize(&str, buflength) == -1) {
			DLog("ERROR _PyString_Resize(0x%x, %ld) == -1", (unsigned int)str, buflength);
			return NULL;
		}
	}
	
	Py_INCREF(str);
	return str;
}


PyDoc_STRVAR(fcgi_Stream_writeByte_DOC,
	"Write a byte to the stream.\n"
	"\n"
	":param  b: The byte to write\n"
	":type   b: int\n"
	":rtype: None\n"
	":raises fcgi.IOError: if the byte could not be written");
PyObject* fcgi_Stream_writeByte(fcgi_Stream* self, PyObject* args)
{
	int rc;
	PyObject* ch;
	
	// Did we get enough arguments?
	if(PyTuple_GET_SIZE(args) == 0) {
		PyErr_SetString(PyExc_TypeError, "writeByte takes exactly 1 argument (0 given)");
		return NULL;
	}
	
	// Save reference to first argument and type check it
	ch = PyTuple_GET_ITEM(args, 0);
	if(!PyInt_Check(ch)) {
		PyErr_SetString(PyExc_TypeError, "first argument must be an integer");
		return NULL;
	}
	
	THREADED(rc = FCGX_PutChar((int)PyInt_AS_LONG(ch), self->stream));
	
	// Check for errors
	if(rc == -1) {
		PyErr_SetString(fcgi_IOError, "Failed to write on stream");
		return NULL;
	}
	
	Py_RETURN_NONE;
}


PyDoc_STRVAR(fcgi_Stream_write_DOC,
	"Write data to the stream.\n"
	"\n"
	"It is guaranteed to write all bytes. If any byte fails to be "
		"written, a fcgi.IOError is raised.\n"
	"\n"
	":type   str:    string\n"
	":param  str:    a string\n"
	":type   length: int\n"
	":param  length: write length bytes from str (optional)\n"
	":rtype: int\n"
	":returns: Number of bytes written\n"
	":raises fcgi.IOError:");
PyObject* fcgi_Stream_write(fcgi_Stream* self, PyObject* args)
{
	//DLog("ENTER fcgi_Stream_write");
	PyObject* str;
	Py_ssize_t length;
	int rc, argc;
	
	argc = PyTuple_GET_SIZE(args);
	
	// Did we get enough arguments?
	if(argc == 0) {
		PyErr_SetString(PyExc_TypeError, "write takes at least 1 argument (0 given)");
		return NULL;
	}
	
	// Save reference to first argument and type check it
	str = PyTuple_GET_ITEM(args, 0);
	if(!PyString_Check(str)) {
		PyErr_SetString(PyExc_TypeError, "First argument must be a string");
		return NULL;
	}
	
	// Figure out length
	if (argc > 1) {
		PyObject* arg1 = PyTuple_GET_ITEM(args, 1);
		if(!PyInt_Check(arg1)) {
			PyErr_SetString(PyExc_TypeError, "Second argument must be an integer");
			return NULL;
		}
		length = PyInt_AS_LONG(arg1);
	}
	else {
		length = PyString_GET_SIZE/*PyString_Size*/(str);
	}
	
	// Write to stream
	if(length)
	{
		THREADED(rc = FCGX_PutStr(/*PyString_AsString*/PyString_AS_STRING(str), length, self->stream));
		
		// Check for errors
		if(rc == -1) {
			PyErr_SetString(fcgi_IOError, "Failed to write on stream");
			return NULL;
		}
	}
	else
		rc = 0;
	
	// Return success
	PyObject* bytes_written = PyInt_FromLong((long)rc);
	Py_INCREF(bytes_written);
	return bytes_written;
}


PyDoc_STRVAR(fcgi_Stream_flush_DOC,
	"Flush the internal buffer. This reduces performance and is "
	"only needed for \"server-push\" applications. The parent request object "
	"always implicitly flushes all it's streams upon finishing the request.\n"
	"\n"
	":rtype: None");
PyObject* fcgi_Stream_flush(fcgi_Stream* self)
{
	THREADED(int rc = FCGX_FFlush(self->stream));
	
	if(rc == -1) {
		PyErr_SetString(fcgi_IOError, "Failed to flush stream");
		return NULL;
	}
	
	Py_RETURN_NONE;
}


PyDoc_STRVAR(fcgi_Stream_close_DOC,
	"Close the stream. You should never need to close a FastCGI "
	"stream, as it's safely handled by the internals of the parent request "
	"object.\n"
	"\n"
	":rtype: None");
PyObject* fcgi_Stream_close(fcgi_Stream* self)
{
	THREADED(int rc = FCGX_FClose(self->stream));
	
	if(rc == -1) {
		PyErr_SetString(fcgi_IOError, "Failed to flush stream");
		return NULL;
	}
	
	Py_RETURN_NONE;
}


// Iteration
PyObject* fcgi_Stream_iter(fcgi_Stream *self)
{
    Py_INCREF(self);
    return (PyObject*)self;
}

PyObject* fcgi_Stream_iternext(fcgi_Stream *self)
{
	PyObject* str = fcgi_Stream_readline(self, NULL);
	if(PyString_GET_SIZE(str) == 0)
	{
		Py_DECREF(str);
		return NULL;
	}
	return str;
}


/********** type configuration **********/

PyDoc_STRVAR(fcgi_Stream_DOC,
	"FastCGI i/o stream");

static PyMethodDef fcgi_Stream_methods[] =
{
	{"close", (PyCFunction)fcgi_Stream_close, METH_NOARGS, fcgi_Stream_close_DOC},
	{"flush", (PyCFunction)fcgi_Stream_flush, METH_NOARGS, fcgi_Stream_flush_DOC},
	
	{"read", (PyCFunction)fcgi_Stream_read, METH_VARARGS, fcgi_Stream_read_DOC},
	{"readline", (PyCFunction)fcgi_Stream_readline, METH_VARARGS, fcgi_Stream_readline_DOC},
	
	{"write", (PyCFunction)fcgi_Stream_write, METH_VARARGS, fcgi_Stream_write_DOC},
	{"writeByte", (PyCFunction)fcgi_Stream_writeByte, METH_VARARGS, fcgi_Stream_writeByte_DOC},
	{NULL}
};

static struct PyMemberDef fcgi_Stream_members[] = {
	{NULL}
};

PyTypeObject fcgi_StreamType = {
	PyObject_HEAD_INIT(NULL)
	0,                         /*ob_size*/
	"fcgi.Stream",             /*tp_name*/
	sizeof(fcgi_Stream),       /*tp_basicsize*/
	0,                         /*tp_itemsize*/
	(destructor)fcgi_Stream_dealloc,        /* tp_dealloc */
	0,                         /*tp_print*/
	0,                         /*tp_getattr*/
	0,                         /*tp_setattr*/
	0,                         /*tp_compare*/
	0,                         /*tp_repr*/
	0,                         /*tp_as_number*/
	0,                         /*tp_as_sequence*/
	0,                         /*tp_as_mapping*/
	0,                         /*tp_hash */
	0,                         /*tp_call*/
	0,                         /*tp_str*/
	0,                         /*tp_getattro*/
	0,                         /*tp_setattro*/
	0,                         /*tp_as_buffer*/
	Py_TPFLAGS_DEFAULT,        /*tp_flags*/
	fcgi_Stream_DOC,           /*tp_doc*/
	0,                                              /* tp_traverse */
	0,                                              /* tp_clear */
	0,                                              /* tp_richcompare */
	0,                                              /* tp_weaklistoffset */
	(getiterfunc)fcgi_Stream_iter,                  /* tp_iter */
	(iternextfunc)fcgi_Stream_iternext,             /* tp_iternext */
	fcgi_Stream_methods,                      /* tp_methods */
	fcgi_Stream_members,                      /* tp_members */
	0,                                              /* tp_getset */
	0,                                              /* tp_base */
	0,                                              /* tp_dict */
	0,                                              /* tp_descr_get */
	0,                                              /* tp_descr_set */
	0,                                              /* tp_dictoffset */
	(initproc)fcgi_Stream_init,               /* tp_init */
	0,                                              /* tp_alloc */
	PyType_GenericNew,                              /* tp_new */
	0                                               /* tp_free */
};

extern int fcgi_Stream_register_types(void)
{
    return PyType_Ready(&fcgi_StreamType);
}
