#ifndef PY_<MODULE>_<CLASS>_H
#define PY_<MODULE>_<CLASS>_H
#include <Python.h>

typedef struct {
    PyObject_HEAD
    /* Type-specific fields go here. */
} <module>_<Class>;

// Type setup
extern PyTypeObject <module>_<Class>Type;
int <module>_<Class>_register_types(void);

// Methods
int <module>_<Class>_init(<module>_<Class>* self, PyObject* args, PyObject* kwargs);
void <module>_<Class>_dealloc(<module>_<Class>* self);

#endif
