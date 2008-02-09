#include "<Class>.h"
#include <structmember.h>

int <module>_<Class>_init(<module>_<Class>* self, PyObject* args, PyObject* kwargs)
{
	return 0;
}

void <module>_<Class>_dealloc(<module>_<Class>* self)
{
}


/********** type configuration **********/

static char <module>_<Class>_doc[] =
PyDoc_STR("");

static PyMethodDef <module>_<Class>_methods[] = {
    {NULL}
};

static struct PyMemberDef <module>_<Class>_members[] = {
    {NULL}
};

PyTypeObject <module>_<Class>Type = {
	PyObject_HEAD_INIT(NULL)
	0,                         /*ob_size*/
	"<module>.<Class>",             /*tp_name*/
	sizeof(<module>_<Class>),       /*tp_basicsize*/
	0,                         /*tp_itemsize*/
	(destructor)<module>_<Class>_dealloc,        /* tp_dealloc */
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
	<module>_<Class>_doc,                /*tp_doc*/
	0,                                              /* tp_traverse */
	0,                                              /* tp_clear */
	0,                                              /* tp_richcompare */
	0,                                              /* tp_weaklistoffset */
	0,                                              /* tp_iter */
	0,                                              /* tp_iternext */
	<module>_<Class>_methods,                       /* tp_methods */
	<module>_<Class>_members,                       /* tp_members */
	0,                                              /* tp_getset */
	0,                                              /* tp_base */
	0,                                              /* tp_dict */
	0,                                              /* tp_descr_get */
	0,                                              /* tp_descr_set */
	0,                                              /* tp_dictoffset */
	(initproc)<module>_<Class>_init,                /* tp_init */
	0,                                              /* tp_alloc */
	PyType_GenericNew,                              /* tp_new */
	0                                               /* tp_free */
};

extern int <module>_<Class>_register_types(void)
{
    return PyType_Ready(&<module>_<Class>Type);
}
