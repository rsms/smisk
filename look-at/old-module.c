#include "module.h"
#include "Request.h"

#include <pthread.h>
#include <sys/types.h>
//#ifdef HAVE_UNISTD_H
#include <unistd.h>
//#endif

//#include <fcgi_config.h>
#include <fcgiapp.h>

PyObject* fcgx_ping(PyObject *self, PyObject *args)
{
	char *arg0;
	if (!PyArg_ParseTuple(args, "s", &arg0))
		return NULL;
	PyObject* s = PyString_FromString(arg0);
	Py_INCREF(s);
	return s;
}

int fcgx_close_fp(FILE* f) {
	// do nothing
	return 0;
}

PyObject* fcgx_accept(PyObject *self, PyObject *args, PyObject* kwargs)
{
	fcgx_Request* request;
	
	// Construct a new Request object
	request = PyObject_New(fcgx_Request, &fcgx_RequestType);
	if (!request) {
		return NULL;
	}
	
	// Init underlying fcgi request
	//FCGX_InitRequest(request->_req, 0, 0);
	
	// Accept
	//static pthread_mutex_t accept_mutex = PTHREAD_MUTEX_INITIALIZER;
	//Some platforms require accept() serialization, some don't. The documentation claims it to be thread safe
	//pthread_mutex_lock(&accept_mutex);
	//int rc = FCGX_Accept_r(request->_req);
	//pthread_mutex_unlock(&accept_mutex);
	
	/*if (rc < 0) {
		// TODO: set error
		break;
	}*/
	
	/*FCGX_FPrintF(request->_req->out,
		"Content-type: text/html\r\n"
		"\r\n"
		"Hello world!");
	
	FCGX_Finish_r(request->_req);*/
	
	// Return NULL on error or None on success
	if (PyErr_Occurred()) {
		Py_DECREF(request);
		return NULL;
	} else {
		Py_INCREF(request);
		return (PyObject*)request;
	}
}


PyObject* fcgx_listen(PyObject *self, PyObject *args, PyObject* kwargs) {
	static char *kwlist[] = {"thread_id", "handler", NULL, NULL};
	
	PyObject *thread_id;
	PyObject *handler;
	
	// Parse arguments
	if (!PyArg_ParseTupleAndKeywords(args, kwargs, "OO", kwlist,
		&thread_id, &handler))
	{
		PyErr_SetString(PyExc_AttributeError,
			"Missing required arguments. Required arguments: INT thread_id, FUNC handler");
		return NULL;
	}
	
	// Sanity-check thread_id
	if(!PyInt_Check(thread_id))
	{
		PyErr_SetString(PyExc_AttributeError, "thread_id must be an integer");
		return NULL;
	}
	
	// Sanity-check handler
	if(!PyCallable_Check(handler))
	{
		PyErr_SetString(PyExc_AttributeError, "handler must be callable");
		return NULL;
	}
	
	// Increase reference count on arguments
	Py_INCREF(thread_id);
	Py_INCREF(handler);
	
	// Vars reused for every request
	int rc;
	FCGX_Request request;
	FCGX_InitRequest(&request, 0, 0);
	
	for (;;)
	{
		// Accept lock
		//static pthread_mutex_t accept_mutex = PTHREAD_MUTEX_INITIALIZER;
		
		//Some platforms require accept() serialization, some don't. The documentation claims it to be thread safe
		//pthread_mutex_lock(&accept_mutex);
		rc = FCGX_Accept_r(&request);
		//pthread_mutex_unlock(&accept_mutex);
		
		/*if (rc < 0) {
			// TODO: set error
			break;
		}*/
		
		// Create stream wrappers
		PyFileObject* outstream;
		outstream = (PyFileObject*)PyFile_FromFile(request.out, "request.out", "w", fcgx_close_fp);
		Py_INCREF(outstream);
		
		// Call user-defined handler
		PyObject* callargs;
		PyObject* callkwargs = NULL;
		PyObject* callresult;
		// void handler(int thread_id, dict request_params, file instream, file outstream, file errstream)
		//callargs = Py_BuildValue("(i)", 123);
		callargs = PyTuple_Pack((Py_ssize_t)5, thread_id, Py_None, Py_None, outstream, Py_None);
		if(callargs == NULL)
		{
			PyErr_SetString(PyExc_MemoryError, "failed to build argument list");
			break;
		}
		
		// Call the handler
		callresult = PyObject_Call(handler, callargs, callkwargs);
		//callresult = PyEval_CallObject(handler, callargs);
		
		// Release args passed to handler
		Py_DECREF(outstream);
		Py_DECREF(callargs);
		
		// Check if handler did exit dirty, if so, an error occured
		if(callresult == NULL) {
			break;
		}
		Py_DECREF(callresult);
		
		// DEBUG
		break;
		
		//server_name = FCGX_GetParam("SERVER_NAME", request.envp);
		
		FCGX_FPrintF(request.out,
			"Content-type: text/html\r\n"
			"\r\n"
			"Hello world on thread_id %d!",
			thread_id);
		
		FCGX_Finish_r(&request);
	}
	
	// Release references for intial arguments
	Py_DECREF(thread_id);
	Py_DECREF(handler);
	
	// Return NULL on error or None on success
	if (PyErr_Occurred()) {
		return NULL;
	} else {
		Py_INCREF(Py_None);
		return Py_None;
	}
}


/* ------------------------------------------------------------------------- */

// static objects at module-level
PyObject* fcgx_Error;

static PyMethodDef module_methods[] = {
    {"ping", (PyCFunction)fcgx_ping, METH_VARARGS, PyDoc_STR("Returns what is put into it.")},
    {"listen", (PyCFunction)fcgx_listen, METH_VARARGS | METH_KEYWORDS, PyDoc_STR("Listen for and handle connections")},
    {"accept", (PyCFunction)fcgx_accept, METH_VARARGS | METH_KEYWORDS, PyDoc_STR("Accept a new connection. Returns a Request object.")},
    {NULL, NULL, 0, NULL} /* Sentinel */
};

PyMODINIT_FUNC initfcgx(void)
{
	PyObject* module;
	
	module = Py_InitModule("fcgx", module_methods);
	
	
	// Register types
	if (!module ||
		//(fcgx_Stream_register_types() < 0) ||
		(fcgx_Request_register_types() < 0)
		)
	{
		return;
	}
	
	Py_INCREF(&fcgx_RequestType);
	PyModule_AddObject(module, "Request", (PyObject *)&fcgx_RequestType);
	
	
	// Setup exceptions
	//if (!(dict = PyModule_GetDict(module))) {
	//	goto error;
	//}
	if (!(fcgx_Error = PyErr_NewException("fcgx.Error", PyExc_StandardError, NULL))) {
		goto error;
	}
	PyModule_AddObject(module, "Error", fcgx_Error);
	//PyDict_SetItemString(dict, "Error", fcgx_Error);
	
	// Initialize FastCGI library
	// TODO: Maybe move this and make it lazy?
	FCGX_Init();
	
error:
	if (PyErr_Occurred())
	{
		PyErr_SetString(PyExc_ImportError, "pysqlite2._sqlite: init failed");
	}
}