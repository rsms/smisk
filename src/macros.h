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


// String macros
#define STR_LTRIM_S(s) \
  for(; *(s)==' '; (s)++);
#define STR_LTRIM_ST(s) \
  for(; (*(s)==' ')||(*(s) == '\t')); s++);
#define STR_LTRIM_STRN(s) \
  for(; (*(s)==' ')||(*(s) == '\t')||(*(s) == '\r')||(*(s) == '\n'); s++);

// String comparison. Inspired by Igor Sysoev.
#if (SMISK_SYS_LITTLE_ENDIAN && SMISK_SYS_NONALIGNED)

#define smisk_str3_cmp(m, c0, c1, c2, c3)                                       \
    *(uint32_t *) m == ((c3 << 24) | (c2 << 16) | (c1 << 8) | c0)

#define smisk_str4cmp(m, c0, c1, c2, c3)                                        \
    *(uint32_t *) m == ((c3 << 24) | (c2 << 16) | (c1 << 8) | c0)

#define smisk_str5cmp(m, c0, c1, c2, c3, c4)                                    \
    *(uint32_t *) m == ((c3 << 24) | (c2 << 16) | (c1 << 8) | c0)             \
        && m[4] == c4

#define smisk_str6cmp(m, c0, c1, c2, c3, c4, c5)                                \
    *(uint32_t *) m == ((c3 << 24) | (c2 << 16) | (c1 << 8) | c0)             \
        && (((uint32_t *) m)[1] & 0xffff) == ((c5 << 8) | c4)

#define smisk_str7_cmp(m, c0, c1, c2, c3, c4, c5, c6, c7)                       \
    *(uint32_t *) m == ((c3 << 24) | (c2 << 16) | (c1 << 8) | c0)             \
        && ((uint32_t *) m)[1] == ((c7 << 24) | (c6 << 16) | (c5 << 8) | c4)

#define smisk_str8cmp(m, c0, c1, c2, c3, c4, c5, c6, c7)                        \
    *(uint32_t *) m == ((c3 << 24) | (c2 << 16) | (c1 << 8) | c0)             \
        && ((uint32_t *) m)[1] == ((c7 << 24) | (c6 << 16) | (c5 << 8) | c4)

#define smisk_str9cmp(m, c0, c1, c2, c3, c4, c5, c6, c7, c8)                    \
    *(uint32_t *) m == ((c3 << 24) | (c2 << 16) | (c1 << 8) | c0)             \
        && ((uint32_t *) m)[1] == ((c7 << 24) | (c6 << 16) | (c5 << 8) | c4)  \
        && m[8] == c8

#else /* !(SMISK_SYS_LITTLE_ENDIAN && SMISK_SYS_NONALIGNED) */

#define smisk_str3_cmp(m, c0, c1, c2, c3)                                       \
    m[0] == c0 && m[1] == c1 && m[2] == c2

#define smisk_str4cmp(m, c0, c1, c2, c3)                                        \
    m[0] == c0 && m[1] == c1 && m[2] == c2 && m[3] == c3

#define smisk_str5cmp(m, c0, c1, c2, c3, c4)                                    \
    m[0] == c0 && m[1] == c1 && m[2] == c2 && m[3] == c3 && m[4] == c4

#define smisk_str6cmp(m, c0, c1, c2, c3, c4, c5)                                \
    m[0] == c0 && m[1] == c1 && m[2] == c2 && m[3] == c3                      \
        && m[4] == c4 && m[5] == c5

#define smisk_str7_cmp(m, c0, c1, c2, c3, c4, c5, c6, c7)                       \
    m[0] == c0 && m[1] == c1 && m[2] == c2 && m[3] == c3                      \
        && m[4] == c4 && m[5] == c5 && m[6] == c6

#define smisk_str8cmp(m, c0, c1, c2, c3, c4, c5, c6, c7)                        \
    m[0] == c0 && m[1] == c1 && m[2] == c2 && m[3] == c3                      \
        && m[4] == c4 && m[5] == c5 && m[6] == c6 && m[7] == c7

#define smisk_str9cmp(m, c0, c1, c2, c3, c4, c5, c6, c7, c8)                    \
    m[0] == c0 && m[1] == c1 && m[2] == c2 && m[3] == c3                      \
        && m[4] == c4 && m[5] == c5 && m[6] == c6 && m[7] == c7 && m[8] == c8

#endif


#endif
