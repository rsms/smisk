/*
Copyright (c) 2007-2008 Rasmus Andersson and contributors

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
#include <stdint.h>

// Types
typedef uint8_t byte;

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

// Module identifier, used in logging
#define MOD_IDENT "smisk.core"

// Replace a PyObject while counting references
#define REPLACE_OBJ(destination, new_value, type) \
  do { \
    type *__old_ ## type ## __LINE__ = (type *)(destination); \
    (destination) = (type *)(new_value); \
    Py_XINCREF(destination); \
    Py_XDECREF(__old_ ## type ## __LINE__); \
  } while (0)

// Ensure a lazy instance variable is available
#define ENSURE_BY_GETTER(direct, getter, ...) \
  if (direct == NULL) {\
    PyObject *tmp = getter;\
    if (tmp == NULL) {\
      __VA_ARGS__ ;\
    } else {\
      Py_DECREF(tmp);\
    }\
  }

#define PyErr_SET_FROM_ERRNO   PyErr_SetFromErrnoWithFilename(PyExc_IOError, __FILE__)

// Log to stderr
#define log_error(fmt, ...) fprintf(stderr, MOD_IDENT " ERROR %s:%d: " fmt "\n", __FILE__, __LINE__, ##__VA_ARGS__)

// Used for temporary debugging
#define _DUMP_REFCOUNT(o) log_error("*** %s: %ld", #o, (o) ? (long int)(o)->ob_refcnt : 0)

// Log to stderr, but only in debug builds
#if SMISK_DEBUG
  #define SMISK_TRACE 1
  #define log_debug(fmt, ...) fprintf(stderr, MOD_IDENT " DEBUG %s:%d: " fmt "\n", __FILE__, __LINE__, ##__VA_ARGS__)
  #define IFDEBUG(x) x
  #define assert_refcount(o, count_test) \
    do { \
      if (!((o)->ob_refcnt count_test)){ \
        log_debug(MOD_IDENT " assert_refcount(%ld, %s)", (Py_ssize_t)(o)->ob_refcnt, #count_test);\
      }\
      assert((o)->ob_refcnt count_test); \
    } while (0);
  #define DUMP_REFCOUNT(o) log_debug(MOD_IDENT " *** %s: %ld", #o, (o) ? (Py_ssize_t)(o)->ob_refcnt : 0)
  #define DUMP_REPR(o) \
    do { PyObject *repr = PyObject_Repr((PyObject *)(o));\
      if (repr) {\
        log_debug(MOD_IDENT " repr(%s) = %s", #o, PyString_AS_STRING(repr));\
        Py_DECREF(repr);\
      } else {\
        log_debug(MOD_IDENT " repr(%s) = <NULL>", #o);\
      }\
    } while (0);
#else
  #define log_debug(fmt, ...) ((void)0)
  #define assert_refcount(o, count_test) 
  #define IFDEBUG(x) 
  #define DUMP_REFCOUNT(o) 
  #define DUMP_REPR(o) 
#endif

#if SMISK_TRACE
  #define log_trace(fmt, ...) fprintf(stderr, MOD_IDENT " TRACE %s:%d in %s " fmt "\n", __FILE__, __LINE__, __FUNCTION__, ##__VA_ARGS__)
  #define IFTRACE(x) x
#else
  #define log_trace(fmt, ...) ((void)0)
  #define IFTRACE(x)
#endif


// Global Python interpreter lock helpers.
//
// Python has a somewhat retarded way of handling threads.
// Even though smisk.core isn't threaded, we need to make
// sure external operations which might block (for example
// FCGX_Accept_r) does not hold on to the global interpreter
// lock.
//
// smisk_py_thstate is defined in __init__.h and implemented
// in __init__.c
#define EXTERN_OP_START \
	smisk_py_thstate = PyThreadState_Swap(NULL); \
	PyEval_ReleaseLock();

#define EXTERN_OP_END \
	PyEval_AcquireLock(); \
	PyThreadState_Swap(smisk_py_thstate);

#define _EXTERN_OP(state_var, section) \
	state_var = PyThreadState_Swap(NULL); \
	PyEval_ReleaseLock(); \
	section; \
	PyEval_AcquireLock(); \
	PyThreadState_Swap(state_var);

// Smisk main state_var
#define EXTERN_OP(section) \
	_EXTERN_OP(smisk_py_thstate, section)

// Temporary state_var
#define EXTERN_OP2(section) \
	_EXTERN_OP(PyThreadState *_thread_state ## __LINE__, section)

// Custom state_var
#define EXTERN_OP3(state_var, section) \
	_EXTERN_OP(state_var, section)
	

// String macros
#define STR_LTRIM_S(s) \
  for (; *(s)==' '; (s)++);
#define STR_LTRIM_ST(s) \
  for (; (*(s)==' ')||(*(s) == '\t')); s++);
#define STR_LTRIM_STRN(s) \
  for (; (*(s)==' ')||(*(s) == '\t')||(*(s) == '\r')||(*(s) == '\n'); s++);

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
