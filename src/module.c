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
#include "Stream.h"

#include <pthread.h>
#include <sys/types.h>
//#ifdef HAVE_UNISTD_H
#include <unistd.h>
//#endif

//#include <fcgi_config.h>
#include <fcgiapp.h>
#include <fastcgi.h>

// Set default listensock
int pyfcgi_listensock_fileno = FCGI_LISTENSOCK_FILENO;


PyDoc_STRVAR(fcgi_shutdown_DOC,
	"Prevent the lib from accepting any new requests. Signal handler safe.\n"
	"\n"
	":rtype: None");
PyObject* fcgi_shutdown(PyObject *self)
{
	FCGX_ShutdownPending();
	Py_RETURN_NONE;
}


PyDoc_STRVAR(fcgi_bind_DOC,
	"Bind to a specific unix socket or host (and/or port).\n"
	"\n"
 	":param path: The Unix domain socket (named pipe for WinNT), hostname, "
		"hostname and port or just a colon followed by a port number. e.g. "
		"\"/tmp/fastcgi/mysocket\", \"www3:5000\", \":5000\"\n"
	":param backlog: The listen queue depth used in the listen() call. "
		"If negative or zero, let system decide (Default if not specified).\n"
	":raises fcgi.IOError: On failure.\n"
	":rtype: None");
PyObject* fcgi_bind(PyObject *self, PyObject *args)
{
	//int FCGX_OpenSocket(const char *path, int backlog)
	int fd, backlog;
	PyObject* path;
	
	// Set default backlog size (<=0 = let system implementation decide)
	backlog = 0;
	
	// Did we get enough arguments?
	if(!args || PyTuple_GET_SIZE(args) < 1)
	{
		PyErr_SetString(PyExc_TypeError, "bind takes at least 1 argument");
		return NULL;
	}
	
	// Save reference to first argument and type check it
	path = PyTuple_GET_ITEM(args, 0);
	if(path == NULL || !PyString_Check(path))
	{
		PyErr_SetString(PyExc_TypeError, "first argument must be a string");
		return NULL;
	}
	
	// Did we get excplicit backlog size?
	if(PyTuple_GET_SIZE(args) > 1)
	{
		PyObject* arg1 = PyTuple_GET_ITEM(args, 1);
		if(arg1 != NULL)
		{
			if(!PyInt_Check(arg1))
			{
				PyErr_SetString(PyExc_TypeError, "second argument must be an integer");
				return NULL;
			}
			backlog = (int)PyInt_AS_LONG(arg1);
		}
	}
	
	// Bind/listen
	fd = FCGX_OpenSocket(PyString_AS_STRING(path), backlog);
	if(fd < 0)
	{
		DLog("ERROR: FCGX_OpenSocket(\"%s\", %d) returned %d. errno: %d", 
			PyString_AS_STRING(path), backlog, fd, errno);
		PyErr_SetString(fcgi_IOError, "failed to bind/listen");
		return NULL;
	}
	
	// Set the process global fileno
	pyfcgi_listensock_fileno = fd;
	
	Py_RETURN_NONE;
}

/* ------------------------------------------------------------------------- */

static PyMethodDef module_methods[] =
{
	{"shutdown", (PyCFunction)fcgi_shutdown, METH_NOARGS,  fcgi_shutdown_DOC},
	{"bind",     (PyCFunction)fcgi_bind,     METH_VARARGS, fcgi_bind_DOC},
	{NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC initfcgi(void)
{
	PyObject* module;
	
	module = Py_InitModule("fcgi", module_methods);
	
	PyEval_InitThreads();
	
	// Register types
	if (!module ||
		(fcgi_Request_register_types() < 0) ||
		(fcgi_Stream_register_types() < 0)
		)
	{
		return;
	}
	
	Py_INCREF(&fcgi_RequestType);
	PyModule_AddObject(module, "Request", (PyObject *)&fcgi_RequestType);
	Py_INCREF(&fcgi_StreamType);
	PyModule_AddObject(module, "Stream", (PyObject *)&fcgi_StreamType);
	
	
	// Setup exceptions
	if (!(fcgi_Error = PyErr_NewException("fcgi.Error", PyExc_StandardError, NULL))) { goto error; }
	PyModule_AddObject(module, "Error", fcgi_Error);
	
	if (!(fcgi_IOError = PyErr_NewException("fcgi.IOError", PyExc_IOError, NULL))) { goto error; }
	PyModule_AddObject(module, "IOError", fcgi_IOError);
	
	if (!(fcgi_AcceptError = PyErr_NewException("fcgi.AcceptError", fcgi_IOError, NULL))) { goto error; }
	PyModule_AddObject(module, "AcceptError", fcgi_AcceptError);
	
	// Initialize FastCGI library
	// TODO: Maybe move this and make it lazy?
	if(FCGX_Init() != 0)
	{
		PyErr_SetString(PyExc_ImportError, "fcgi: FCGX_Init() != 0");
		return;
	}
	
error:
	if (PyErr_Occurred())
	{
		PyErr_SetString(PyExc_ImportError, "fcgi: init failed");
	}
}