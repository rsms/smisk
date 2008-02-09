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
#include "NotificationCenter.h"
#include <structmember.h>


// for internal use
PyObject* smisk_NotificationCenter_postc( smisk_NotificationCenter* self, 
                                         PyObject* args )
{  
  Py_ssize_t listSize, i;
  PyObject* notificationList;
  PyObject* observer;
  
  if((notificationList = PyDict_GetItem(self->observers, PyTuple_GET_ITEM(args, 0))) == NULL) {
    DLog("No observers for notification '%s'", PyString_AS_STRING(PyTuple_GET_ITEM(args, 0)));
    Py_RETURN_NONE;
  }
  
  listSize = PyList_GET_SIZE(notificationList);
  
  for(i=0;i<listSize;i++) {
    if((observer = PyList_GetItem(notificationList, i)) == NULL) {
      DLog("list index error");
      return NULL;
    }
    if(PyObject_Call(observer, args, NULL) == NULL) {
      DLog("error in observer during posting of notification");
      return NULL;
    }
  }
  
  Py_RETURN_NONE;
}


/************************* class methods *****************************/

PyObject* smisk_NotificationCenter_default_instance = NULL;

PyObject* smisk_NotificationCenter_default(PyObject* cls)
{
  DLog("ENTER smisk_NotificationCenter_default");
  if(!smisk_NotificationCenter_default_instance) {
    smisk_NotificationCenter_default_instance = PyObject_Call((PyObject*)&smisk_NotificationCenterType, NULL, NULL);
  }
  Py_INCREF(smisk_NotificationCenter_default_instance);
  return smisk_NotificationCenter_default_instance;
}


/************************* instance methods *****************************/

int smisk_NotificationCenter_init(smisk_NotificationCenter* self, PyObject* args, PyObject* kwargs)
{
  DLog("ENTER smisk_NotificationCenter_init");
  
  // Construct a new observers dict
  self->observers = PyDict_New();
  if (self->observers == NULL)
  {
    DLog("self->observers == NULL");
    Py_DECREF(self);
    return -1;
  }
  
  return 0;
}


void smisk_NotificationCenter_dealloc(smisk_NotificationCenter* self)
{
  DLog("ENTER smisk_NotificationCenter_dealloc");
  Py_DECREF(self->observers);
}


PyDoc_STRVAR(smisk_NotificationCenter_subscribe_DOC,
  "Subscribe observer.\n"
  "\n"
  ":param observer:     Callable object\n"
  ":type  observer:     object\n"
  ":param notification: Notification\n"
  ":type  notification: string\n"
  ":rtype: None");
PyObject* smisk_NotificationCenter_subscribe(smisk_NotificationCenter* self, PyObject* args)
{
  DLog("ENTER smisk_NotificationCenter_subscribe");
  
  int rc;
  PyObject* observer;         // PyObject
  PyObject* notification;     // PyStringObject
  PyObject* notificationList; // PyListObject
  
  // Did we get enough arguments?
  if(PyTuple_GET_SIZE(args) != 2) {
    PyErr_SetString(PyExc_TypeError, "subscribe takes exactly 2 arguments");
    return NULL;
  }
  
  // Save reference to first argument and type check it
  observer = PyTuple_GET_ITEM(args, 0);
  if(!observer || observer == Py_None) {
    PyErr_SetString(PyExc_TypeError, "first argument must be a valid object");
    return NULL;
  }
  if(!PyCallable_Check(observer)) {
    PyErr_SetString(PyExc_TypeError, "first argument must be callable");
    return NULL;
  }
  notification = PyTuple_GET_ITEM(args, 1);
  if(!notification || !PyString_Check(notification)) {
    PyErr_SetString(PyExc_TypeError, "second argument must be a string");
    return NULL;
  }
  
  // Need to create new list for observers[notification]?
  if((rc = PyDict_Contains(self->observers, notification)) != 1) {
    if(rc == -1) {
      DLog("PyDict_Contains(self->observers, notification) == -1");
      return NULL;
    }
    notificationList = PyList_New(0);
    if(notificationList == NULL) {
      DLog("(notificationList = PyList_New()) == NULL");
      return NULL;
    }
    rc = PyDict_SetItem(self->observers, notification, notificationList);
  }
  else {
    notificationList = PyDict_GetItem(self->observers, notification);
    if(notificationList == NULL) {
      DLog("(notificationList = PyDict_GetItem(self->observers, notification)) == NULL");
      return NULL;
    }
  }
  
  // Add observer
  if(PyList_Append(notificationList, observer) == -1) {
    DLog("PyList_Append(notificationList, observer) == -1");
    return NULL;
  }
  
  Py_RETURN_NONE;
}


PyDoc_STRVAR(smisk_NotificationCenter_unsubscribe_DOC,
  "Unsubscribe observer.\n"
  "\n"
  ":rtype: None");
PyObject* smisk_NotificationCenter_unsubscribe(smisk_NotificationCenter* self, PyObject* args)
{
  DLog("ENTER smisk_NotificationCenter_unsubscribe");
  Py_RETURN_NONE;
}


PyDoc_STRVAR(smisk_NotificationCenter_post_DOC,
  "Service a error message.\n"
  "\n"
  ":rtype: None");
PyObject* smisk_NotificationCenter_post(smisk_NotificationCenter* self, PyObject* args)
{
  DLog("ENTER smisk_NotificationCenter_post");
  
  PyObject* notification; // PyStringObject
  
  // Did we get enough arguments?
  if(PyTuple_GET_SIZE(args) < 1) {
    PyErr_SetString(PyExc_TypeError, "post takes at least 1 argument");
    return NULL;
  }
  
  // Save reference to first argument and type check it
  notification = PyTuple_GET_ITEM(args, 0);
  if(!notification || !PyString_Check(notification)) {
    PyErr_SetString(PyExc_TypeError, "first argument must be a string");
    return NULL;
  }
  
  return smisk_NotificationCenter_postc(self, args);
}


/********** type configuration **********/

PyDoc_STRVAR(smisk_NotificationCenter_DOC,
  "Notification center implementing process wide observation.\n"
  "\n"
  ":ivar observers:  Observers keyed by notification\n"
  ":type observers:  dict\n");

// Methods
static PyMethodDef smisk_NotificationCenter_methods[] =
{
  {"subscribe",   (PyCFunction)smisk_NotificationCenter_subscribe,   METH_VARARGS,           smisk_NotificationCenter_subscribe_DOC},
  {"unsubscribe", (PyCFunction)smisk_NotificationCenter_unsubscribe, METH_VARARGS,           smisk_NotificationCenter_unsubscribe_DOC},
  {"post",        (PyCFunction)smisk_NotificationCenter_post,        METH_VARARGS,           smisk_NotificationCenter_post_DOC},
  {"default",     (PyCFunction)smisk_NotificationCenter_default,     METH_CLASS|METH_NOARGS, NULL},
  {NULL}
};

// Class members
static struct PyMemberDef smisk_NotificationCenter_members[] =
{
  {"observers", T_OBJECT_EX, offsetof(smisk_NotificationCenter, observers), RO, NULL},
  {NULL}
};

// Type definition
PyTypeObject smisk_NotificationCenterType = {
  PyObject_HEAD_INIT(&PyType_Type)
  0,             /*ob_size*/
  "smisk.NotificationCenter", /*tp_name*/
  sizeof(smisk_NotificationCenter),     /*tp_basicsize*/
  0,             /*tp_itemsize*/
  (destructor)smisk_NotificationCenter_dealloc,    /* tp_dealloc */
  0,             /*tp_print*/
  0,             /*tp_getattr*/
  0,             /*tp_setattr*/
  0,             /*tp_compare*/
  0,             /*tp_repr*/
  0,             /*tp_as_number*/
  0,             /*tp_as_sequence*/
  0,             /*tp_as_mapping*/
  0,             /*tp_hash */
  0,             /*tp_call*/
  0,             /*tp_str*/
  0,             /*tp_getattro*/
  0,             /*tp_setattro*/
  0,             /*tp_as_buffer*/
  Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE, /*tp_flags*/
  smisk_NotificationCenter_DOC,      /*tp_doc*/
  (traverseproc)0,       /* tp_traverse */
  0,             /* tp_clear */
  0,             /* tp_richcompare */
  0,             /* tp_weaklistoffset */
  0,             /* tp_iter */
  0,             /* tp_iternext */
  smisk_NotificationCenter_methods,  /* tp_methods */
  smisk_NotificationCenter_members,  /* tp_members */
  0,               /* tp_getset */
  0,               /* tp_base */
  0,               /* tp_dict */
  0,               /* tp_descr_get */
  0,               /* tp_descr_set */
  0,               /* tp_dictoffset */
  (initproc)smisk_NotificationCenter_init, /* tp_init */
  0,               /* tp_alloc */
  PyType_GenericNew,  /* tp_new */
  0              /* tp_free */
};

extern int smisk_NotificationCenter_register_types(void)
{
  return PyType_Ready(&smisk_NotificationCenterType);
}
