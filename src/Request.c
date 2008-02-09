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
#include "module.h"
#include "Request.h"
#include <structmember.h>
#include <fastcgi.h>

static inline void _fcgi_Request_finish_if_needed(fcgi_Request* self)
{
	if(self->state != FCGI_REQUEST_STATE_FINISHED)
	{
		THREADED( FCGX_Finish_r(&self->req) );
		self->state = FCGI_REQUEST_STATE_FINISHED;
	}
}

int fcgi_Request_init(fcgi_Request* self, PyObject* args, PyObject* kwargs)
{
	DLog("ENTER fcgi_Request_init");
	
	self->state = FCGI_REQUEST_STATE_NEVER_ACCEPTED;
	
	// Nullify some members
	self->params = NULL;
	self->envp_buf = NULL;
	
	// Init underlying fcgi request
	// Setting last argument to FCGI_FAIL_ACCEPT_ON_INTR prevents FCGI_Accept()
	// from restarting upon being interrupted.
	if(FCGX_InitRequest(&self->req, pyfcgi_listensock_fileno, FCGI_FAIL_ACCEPT_ON_INTR))
	{
		DLog("FCGI_InitRequest(&self->req, 0, 0) != 0");
		PyErr_SetString(fcgi_Error, "Failed to initialize fcgi host-to-app connection");
		Py_DECREF(self);
		return -1;
	}
	
	// Construct a new Stream for in
	self->input = (fcgi_Stream*)PyObject_Call((PyObject*)&fcgi_StreamType, NULL, NULL);
	if (self->input == NULL)
	{
		DLog("self->input == NULL");
		Py_DECREF(self);
		return -1;
	}
	
	// Construct a new Stream for out
	self->out = (fcgi_Stream*)PyObject_Call((PyObject*)&fcgi_StreamType, NULL, NULL);
	if (self->out == NULL)
	{
		DLog("self->out == NULL");
		Py_DECREF(self);
		return -1;
	}
	
	// Construct a new Stream for err
	self->err = (fcgi_Stream*)PyObject_Call((PyObject*)&fcgi_StreamType, NULL, NULL);
	if (self->err == NULL)
	{
		DLog("self->err == NULL");
		Py_DECREF(self);
		return -1;
	}
	
	return 0;
}

void fcgi_Request_dealloc(fcgi_Request* self)
{
	DLog("ENTER fcgi_Request_dealloc");
	
	_fcgi_Request_finish_if_needed(self);
	
	Py_XDECREF(self->input);
	Py_XDECREF(self->out);
	Py_XDECREF(self->err);
	Py_XDECREF(self->params);
	
	// free envp buf
	if(self->envp_buf)
		free(self->envp_buf);
	
	// free request internals (this also frees internals of streams. That's
	// why we don't do anything in stream deallocs.
	THREADED(FCGX_Free(&self->req, /*close*/1));
}

PyDoc_STRVAR(fcgi_Request_accept_DOC,
	"Wait for and accept a new connection.\n"
	"Sending SIGUSR1 to a process will have the same effect as calling "
	"fcgi.shutdown(), thus not accepting any new connections.\n"
	"\n"
	":rtype: None");
PyObject* fcgi_Request_accept(fcgi_Request* self)
{
	int rc;
	
	// Accept (will finish the request first, if not already finished)
	THREADED(rc = FCGX_Accept_r(&self->req));
	
	// Reference streams
	// We want to do this asap because some stupid ass maybe saved a reference
	// to a stream in python and if he is actiong on it before we have set the
	// references correctly (they are freed and reallocated at each accept) he
	// will get trouble, aka krasch boom bang.
	self->input->stream = self->req.in;
	self->out->stream = self->req.out;
	self->err->stream = self->req.err;
	
	// Check accept error
	if (rc != 0)
	{
		if(FCGX_IsCGI()) {
			PyErr_SetString(fcgi_Error, "Must be run in a FastCGI environment");
		}
		else if(rc < 0)
		{
			PyErr_SetString(fcgi_AcceptError,
				"Server is shutting down or a previous accept error occured "
				"earlier in the same thread.");
		}
		else {
			DLog("FCGX_Accept_r(&self->req) returned %d", rc);
			PyErr_SetString(fcgi_IOError, "Accept failed");
		}
		return NULL;
	}
	
	//DLog("self->req.keepConnection: %d", self->req.keepConnection);
	
	// Set state
	self->state = FCGI_REQUEST_STATE_ACCEPTED;
	
	// We have new parameters
	if(self->params) {
		Py_DECREF(self->params);
		self->params = NULL;
	}
	
	Py_INCREF(self);
	return (PyObject*)self;
}


PyDoc_STRVAR(fcgi_Request_commit_DOC,
	"Commit request. Tell host server this request has been handled.\n"
	"\n"
	":rtype: None");
PyObject* fcgi_Request_commit(fcgi_Request* self)
{
	// Raise error if already commited
	if(self->state == FCGI_REQUEST_STATE_FINISHED)
	{
		PyErr_SetString(fcgi_Error, "Already committed");
		return NULL;
	}
	
	_fcgi_Request_finish_if_needed(self);
	
	Py_RETURN_NONE;
}


PyDoc_STRVAR(fcgi_Request_sendfile_DOC,
	"Send a file to the client in a performance optimal way.\n"
	"\n"
	"If sendfile functionality is not available or not supported by the host "
	"server, this will fail silently. (Sorry for that!)\n"
	"\n"
	"Currently only lighttpd is supported through X-LIGHTTPD-send-file header.\n"
	"\n"
	"This method must be called before any body output has been sent.\n"
	"\n"
	":param  filename: If this is a relative path, it's relative to the host server root.\n"
	":type   filename: string\n"
	":raises fcgi.IOError: if something i/o failed.\n"
	":rtype: None");
PyObject* fcgi_Request_sendfile(fcgi_Request* self, PyObject* args)
{
	int rc;
	PyObject* filename;
	
	// Did we get enough arguments?
	if(PyTuple_GET_SIZE(args) != 1) {
		PyErr_SetString(PyExc_TypeError, "writeByte takes exactly 1 argument");
		return NULL;
	}
	
	// Save reference to first argument and type check it
	filename = PyTuple_GET_ITEM(args, 0);
	if(!PyString_Check(filename)) {
		PyErr_SetString(PyExc_TypeError, "first argument must be a string");
		return NULL;
	}
	
	// TODO: Needs to handle all kinds of hosts (apache, etc) not only lighttpd
	
	THREADED_START;
	FCGX_PutStr("X-LIGHTTPD-send-file: ", 22, self->out->stream);
	FCGX_PutStr(PyString_AsString(filename), PyString_Size(filename), self->out->stream);
	rc = FCGX_PutStr("\r\n\r\n", 4, self->out->stream);
	THREADED_END;
	
	// Check for errors
	if(rc == -1) {
		PyErr_SetString(fcgi_IOError, "Failed to write on stream");
		return NULL;
	}
	
	Py_RETURN_NONE;
}


PyObject* fcgi_Request_get_params(fcgi_Request* self)
{
	//DLog("ENTER fcgi_Request_get_params");
	
	// Lazy initializer
	if(self->params == NULL)
	{
		self->params = (PyDictObject*)PyDict_New();
		if(self->params == NULL) {
			DLog("self->params == NULL");
			return NULL;
		}
		
		// Transcribe envp to dict
		if(self->req.envp != NULL)
		{
			char **p;
			char *x;
			PyStringObject* k;
			PyStringObject* v;
			size_t bufi;
			
			// Allocate envp copy buffer if needed (only done once per Request instance)
			if(self->envp_buf == NULL) {
				DLog("Lazy-Allocating get params key/value buffer");
				self->envp_buf = (char *)malloc(sizeof(char)*FCGI_REQUEST_ENVP_BUF_SIZE);
			}
			
			for (p = self->req.envp; *p; ++p)
			{
				k = v = NULL;
				
				// read key
				bufi = 0;
				for (x = *p; *x || bufi == FCGI_REQUEST_ENVP_BUF_SIZE; ++x) {
					//DLog("k: %c  %03d 0x%02x", *x, *x, *x);
					if(*x == (char)61) {
						x++;
						break;
					}
					self->envp_buf[bufi++] = *x;
				}
				k = (PyStringObject *)PyString_FromStringAndSize(self->envp_buf, bufi);
				if(k == NULL) {
					DLog("ERROR: Failed to create string");
					break;
				}
				
				// protection for buffer overflow
				if(bufi >= FCGI_REQUEST_ENVP_BUF_SIZE) {
					DLog("ERROR: Bailing out before buffer overflows");
					PyErr_SetString(fcgi_Error, "Buffer overflow avoided in fcgi_Request_get_params(), " __FILE__);
					break;
				}
				
				// read value
				bufi = 0;
				for (; *x; ++x) {
					//DLog("v: %c  %03d 0x%02x", *x, *x, *x);
					self->envp_buf[bufi++] = *x;
				}
				v = (PyStringObject *)PyString_FromStringAndSize(self->envp_buf, bufi);
				if(v == NULL) {
					DLog("ERROR: Failed to create string");
					Py_DECREF(k);
					break;
				}
				
				// Found anything?
				if(bufi)
				{
					if( PyDict_SetItem((PyObject*)self->params, (PyObject *)k, (PyObject *)v) )
					{
						DLog("PyDict_SetItem() != 0");
						return NULL;
					}
				}
				//else
				//{
				Py_DECREF(k);
				Py_DECREF(v);
				//}
			}
			
			// If an error occured...
			if (PyErr_Occurred()) {
				DLog("PyErr_Occurred() == TRUE");
				return NULL;
			}
		}
		
		// Make read-only
		//self->params = (PyDictObject*)PyDictProxy_New((PyObject*)self->params);
	}
	
	Py_INCREF(self->params);
	return (PyObject*)self->params;
}


/********** type configuration **********/

PyDoc_STRVAR(fcgi_Request_DOC,
	"A FastCGI request\n"
	"\n"
	":ivar input:  Input stream\n"
	":type input:  fcgi.Stream\n"
	":ivar out:    Output stream\n"
	":type out:    fcgi.Stream\n"
	":ivar err:    Error output stream\n"
	":type err:    fcgi.Stream\n"
	":ivar params: Request parameters, equivalent to the ``env`` in CGI.\n"
	":type params: dict");

// Methods
static PyMethodDef fcgi_Request_methods[] =
{
	{"accept",   (PyCFunction)fcgi_Request_accept,   METH_NOARGS, fcgi_Request_accept_DOC},
	{"commit",   (PyCFunction)fcgi_Request_commit,   METH_NOARGS,  fcgi_Request_commit_DOC},
	{"sendfile", (PyCFunction)fcgi_Request_sendfile, METH_VARARGS, fcgi_Request_sendfile_DOC},
	{NULL}
};

// Properties
static PyGetSetDef fcgi_Request_getset[] = {
    //{"params",  (getter)pysqlite_connection_get_params, (setter)pysqlite_connection_set_isolation_level},
    {"params", (getter)fcgi_Request_get_params, (setter)0},
    {NULL}
};

// Class members
static struct PyMemberDef fcgi_Request_members[] =
{
	{"input", T_OBJECT_EX, offsetof(fcgi_Request, input), RO, NULL},
	{"out",   T_OBJECT_EX, offsetof(fcgi_Request, out),   RO, NULL},
	{"err",   T_OBJECT_EX, offsetof(fcgi_Request, err),   RO, NULL},
	{NULL}
};

// Type definition
PyTypeObject fcgi_RequestType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,                         /*ob_size*/
	"fcgi.Request",             /*tp_name*/
	sizeof(fcgi_Request),       /*tp_basicsize*/
	0,                         /*tp_itemsize*/
	(destructor)fcgi_Request_dealloc,        /* tp_dealloc */
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
	Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE, /*tp_flags*/
	fcgi_Request_DOC,          /*tp_doc*/
	(traverseproc)0,           /* tp_traverse */
	0,                         /* tp_clear */
	0,                         /* tp_richcompare */
	0,                         /* tp_weaklistoffset */
	0,                         /* tp_iter */
	0,                         /* tp_iternext */
	fcgi_Request_methods,      /* tp_methods */
	fcgi_Request_members,      /* tp_members */
	fcgi_Request_getset,         /* tp_getset */
	0,                           /* tp_base */
	0,                           /* tp_dict */
	0,                           /* tp_descr_get */
	0,                           /* tp_descr_set */
	0,                           /* tp_dictoffset */
	(initproc)fcgi_Request_init, /* tp_init */
	0,                           /* tp_alloc */
	PyType_GenericNew,           /* tp_new */
	0                            /* tp_free */
};

extern int fcgi_Request_register_types(void)
{
    return PyType_Ready(&fcgi_RequestType);
}
