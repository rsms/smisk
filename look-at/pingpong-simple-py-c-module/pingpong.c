/*
 * threaded.c -- A simple multi-threaded FastCGI application.
 */

#include <Python.h>


PyObject *pingpong_ping(PyObject *self, PyObject *args)
{
	char *arg0;
	if (!PyArg_ParseTuple(args, "s", &arg0))
		return NULL;
	
	PyObject* s = PyString_FromString(arg0);
	Py_INCREF(s);
	return s;
}


/* ------- */
static PyMethodDef _methods[] = {
    {"ping",  pingpong_ping, METH_VARARGS, "Takes a string and returns it."},
    {NULL, NULL, 0, NULL} /* Sentinel */
};

PyMODINIT_FUNC initpingpong(void)
{
	(void) Py_InitModule("pingpong", _methods);
}