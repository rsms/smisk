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
#ifndef PY_FCGI_MODULE_H
#define PY_FCGI_MODULE_H
// version is replaced at build-time, so no manual edits.
#include "version.h"
#include <Python.h>

extern int pyfcgi_listensock_fileno;

// static objects at module-level
PyObject* fcgi_Error; // extends PyExc_StandardError
PyObject* fcgi_IOError; // extends PyExc_IOError
PyObject* fcgi_AcceptError; // extends fcgi_IOError

// Utils
#ifdef DEBUG
	#define DLog(fmt, ...) fprintf(stderr, __FILE__ ":%d: " fmt "\n", __LINE__, ##__VA_ARGS__)
#else
	#define DLog(fmt, ...)
#endif


#define THREADED_START \
	PyThreadState *_thread_state = PyThreadState_Swap(NULL); \
	PyEval_ReleaseLock();

#define THREADED_END \
	PyEval_AcquireLock(); \
	PyThreadState_Swap(_thread_state);

#define _THREADED(section, state_var) \
	PyThreadState *state_var = PyThreadState_Swap(NULL); \
	PyEval_ReleaseLock(); \
	section; \
	PyEval_AcquireLock(); \
	PyThreadState_Swap(state_var);

#define THREADED(section) \
	_THREADED(section, _thread_state ## __LINE__)

#endif
