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
#ifndef SMISK_MACROS_H
#define SMISK_MACROS_H

#include <Python.h>

/* Convert an ASCII hex digit to the corresponding number between 0
   and 15.  H should be a hexadecimal digit that satisfies isxdigit;
   otherwise, the result is undefined.  */
#define XDIGIT_TO_NUM(h) ((h) < 'A' ? (h) - '0' : toupper(h) - 'A' + 10)
#define X2DIGITS_TO_NUM(h1, h2) ((XDIGIT_TO_NUM (h1) << 4) + XDIGIT_TO_NUM (h2))

/* The reverse of the above: convert a number in the [0, 16) range to
   the ASCII representation of the corresponding hexadecimal digit.
   `+ 0' is there so you can't accidentally use it as an lvalue.  */
#define XNUM_TO_DIGIT(x) ("0123456789ABCDEF"[x] + 0)
#define XNUM_TO_digit(x) ("0123456789abcdef"[x] + 0)


// Py 2.4 compat
#if (PY_MAJOR_VERSION == 2 && PY_MINOR_VERSION < 5)
#define Py_ssize_t ssize_t
#endif

// Get minimum value
#ifndef min
#define min(X, Y)  ((X) < (Y) ? (X) : (Y))
#endif
#ifndef max
#define max(X, Y)  ((X) > (Y) ? (X) : (Y))
#endif

// Replace a PyObject while counting references
#define REPLACE_OBJ(to, expr, type) \
  do { type *__replace_obj = (type *)(to); \
  (to) = (type *)(expr); \
  Py_XINCREF(to); \
  Py_XDECREF(__replace_obj); } while(0)

// Ensure a lazy instance variable is available
#define ENSURE_BY_GETTER(direct, getter, ...) \
  if(direct == NULL) {\
    PyObject *tmp = getter;\
    if(tmp == NULL) {\
      __VA_ARGS__ ;\
    } else {\
      Py_DECREF(tmp);\
    }\
  }

#define PyErr_SET_FROM_ERRNO   PyErr_SetFromErrnoWithFilename(PyExc_IOError, __FILE__)

// Log to stderr
#define log_error(fmt, ...) fprintf(stderr, "%s:%d: " fmt "\n", __FILE__, __LINE__, ##__VA_ARGS__)

// Used for temporary debugging
#define _DUMP_REFCOUNT(o) log_error("*** %s: %ld", #o, (o) ? (long int)(o)->ob_refcnt : 0)

// Log to stderr, but only in debug builds
#if SMISK_DEBUG
  #define log_debug(fmt, ...) fprintf(stderr, "DEBUG %s:%d: " fmt "\n", __FILE__, __LINE__, ##__VA_ARGS__)
  #define IFDEBUG(x) x
  #define assert_refcount(o, count_test) \
    if(!((o)->ob_refcnt count_test)){ log_debug("assert_refcount(%ld %s)", (Py_ssize_t)(o)->ob_refcnt, #count_test); }\
    assert((o)->ob_refcnt count_test)
  #define DUMP_REFCOUNT(o) log_debug("*** %s: %ld", #o, (o) ? (Py_ssize_t)(o)->ob_refcnt : 0)
  #define DUMP_REPR(o) \
    do { PyObject *repr = PyObject_Repr((PyObject *)(o));\
      if(repr) {\
        log_debug("repr(%s) = %s", #o, PyString_AS_STRING(repr));\
        Py_DECREF(repr);\
      } else {\
        log_debug("repr(%s) = <NULL>", #o);\
      }\
    } while(0);
#else
  #define log_debug(fmt, ...) ((void)0)
  #define assert_refcount(o, count_test) 
  #define IFDEBUG(x) 
  #define DUMP_REFCOUNT(o) 
  #define DUMP_REPR(o) 
#endif


// STR macros
#define STR_LTRIM_S(s) \
  for(; *(s)==' '; (s)++);
#define STR_LTRIM_ST(s) \
  for(; (*(s)==' ')||(*(s) == '\t')); s++);
#define STR_LTRIM_STRN(s) \
  for(; (*(s)==' ')||(*(s) == '\t')||(*(s) == '\r')||(*(s) == '\n'); s++);


// STR_EQUALS macros
#define STR_EQUALS_2(x,y) ( ((x)[0]==(y)[0])&&((x)[1]==(y)[1]) )
#define STR_EQUALS_3(x,y) ( ((x)[0]==(y)[0])&&((x)[1]==(y)[1])&&((x)[2]==(y)[2]) )
#define STR_EQUALS_4(x,y) ( ((x)[0]==(y)[0])&&((x)[1]==(y)[1])&&((x)[2]==(y)[2])&&((x)[3]==(y)[3]) )
#define STR_EQUALS_5(x,y) ( ((x)[0]==(y)[0])&&((x)[1]==(y)[1])&&((x)[2]==(y)[2])&&((x)[3]==(y)[3])&&((x)[4]==(y)[4]) )
#define STR_EQUALS_6(x,y) ( ((x)[0]==(y)[0])&&((x)[1]==(y)[1])&&((x)[2]==(y)[2])&&((x)[3]==(y)[3])&&((x)[4]==(y)[4])&&((x)[5]==(y)[5]) )
#define STR_EQUALS_7(x,y) ( ((x)[0]==(y)[0])&&((x)[1]==(y)[1])&&((x)[2]==(y)[2])&&((x)[3]==(y)[3])&&((x)[4]==(y)[4])&&((x)[5]==(y)[5])&&((x)[6]==(y)[6]) )
#define STR_EQUALS_8(x,y) ( ((x)[0]==(y)[0])&&((x)[1]==(y)[1])&&((x)[2]==(y)[2])&&((x)[3]==(y)[3])&&((x)[4]==(y)[4])&&((x)[5]==(y)[5])&&((x)[6]==(y)[6])&&((x)[7]==(y)[7]) )
#define STR_EQUALS_9(x,y) ( ((x)[0]==(y)[0])&&((x)[1]==(y)[1])&&((x)[2]==(y)[2])&&((x)[3]==(y)[3])&&((x)[4]==(y)[4])&&((x)[5]==(y)[5])&&((x)[6]==(y)[6])&&((x)[7]==(y)[7])&&((x)[8]==(y)[8]) )
#define STR_EQUALS_10(x,y) ( ((x)[0]==(y)[0])&&((x)[1]==(y)[1])&&((x)[2]==(y)[2])&&((x)[3]==(y)[3])&&((x)[4]==(y)[4])&&((x)[5]==(y)[5])&&((x)[6]==(y)[6])&&((x)[7]==(y)[7])&&((x)[8]==(y)[8])&&((x)[9]==(y)[9]) )


#endif
