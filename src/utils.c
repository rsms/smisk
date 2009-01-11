/*
Copyright (c) 2007-2009 Rasmus Andersson

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

#include <stdlib.h>
#include <time.h>
#include <ctype.h> /* tolower() */
#if HAVE_SYS_TIME_H
#include <sys/time.h>
#endif

#include <fcgiapp.h>
#include <Python.h>
#include <marshal.h> /* for smisk_object_hash */

#include "utils.h"
#include "__init__.h"
#include "URL.h"


PyObject *smisk_PyString_FromStringAndSize_lower(const char *src, Py_ssize_t length) {
  PyObject *dst;
  char *dst_p;
  Py_ssize_t i;
  
  if ((dst = PyString_FromStringAndSize(NULL, length)) == NULL)
    return NULL;
  
  dst_p = PyString_AS_STRING(dst);
  
  for (i = 0; i < length; i++) {
    *dst_p = tolower((char)src[i]);
    dst_p++;
  }
  
  return dst;
}


// Returns PyStringObject (new reference)
PyObject *smisk_format_exc(PyObject *type, PyObject *value, PyObject *tb) {
  PyObject *msg = NULL;
  PyObject *lines = NULL;
  PyObject *traceback = NULL;
  PyObject *format_exception = NULL;
  
  if (type == NULL) {
    log_debug("No error occured. type == NULL");
    Py_RETURN_NONE;
  }
  assert(value != NULL);
  assert(tb != NULL);
  
  if ( (traceback = PyImport_ImportModule("traceback")) == NULL ) {
    log_debug("PyImport_ImportModule('traceback') == NULL");
    return NULL;
  }
  
  if ( (format_exception = PyObject_GetAttrString(traceback, "format_exception")) == NULL ) {
    log_debug("PyObject_GetAttrString(traceback, 'format_exception') == NULL");
    Py_DECREF(traceback);
    return NULL;
  }
  Py_DECREF(traceback);
  
  if ( (lines = PyObject_CallFunctionObjArgs(format_exception, type, value, tb, NULL)) == NULL ) {
    log_debug("PyObject_CallFunctionObjArgs(format_exception...) == NULL");
    Py_DECREF(format_exception);
    return NULL;
  }
  Py_DECREF(format_exception);
  
  msg = PyString_FromString("");
  Py_ssize_t i = 0, lines_len = PyList_GET_SIZE(lines);
  for (; i < lines_len; i++) {
    PyString_ConcatAndDel(&msg, PyList_GET_ITEM(lines, i));
    if (msg == NULL) {
      log_debug("msg == NULL");
      Py_DECREF(lines);
      return NULL;
    }
  }
  
  return msg;
}


int PyDict_assoc_val_with_key(PyObject *dict, PyObject *val, PyObject *key) {
  PyObject *existing_val, *new_val;
  
  if (PyDict_Contains(dict, key)) {
    // multi-value
    existing_val = PyDict_GetItem(dict, key);
    
    if (PyList_CheckExact(existing_val)) {
      // just append
      if (PyList_Append(existing_val, val) != 0) {
        return -1;
      }
    }
    else {
      // convert to list
      new_val = PyList_New(2);
      PyList_SET_ITEM(new_val, 0, existing_val);
      PyList_SET_ITEM(new_val, 1, val);
      Py_INCREF(existing_val); // Since we want to keep it and PyList_SET_ITEM did not INCREF
      Py_INCREF(val); // Since we want to keep it and PyList_SET_ITEM did not INCREF
      
      if (PyDict_SetItem(dict, key, new_val) != 0)
        return -1;
      
      assert_refcount(new_val, > 1);
      Py_DECREF(new_val); // we don't own it anymore
    }
  }
  else { // key is unique as far as we know
    if (PyDict_SetItem(dict, key, val) != 0) {
      return -1;
    }
  }
  
  assert_refcount(val, > 1);
  return 0;
}


int smisk_parse_input_data( char *s,
                            const char *separator,
                            int is_cookie_data, 
                            PyObject *dict,
                            const char *charset )
{
  char *scpy, *key, *val, *strtok_ctx = NULL;
  PyObject *py_key, *py_val;
  int status = 0;
  
  log_debug("smisk_parse_input_data '%s' charset=%s", 
            s, (charset ? charset : "NULL") );
  
  scpy = strdup(s);
  key = strtok_r(scpy, separator, &strtok_ctx);
  
  while (key) {
    val = strchr(key, '=');
    
    if (is_cookie_data) {
      // Remove leading spaces from cookie names, needed for multi-cookie 
      // header where ; can be followed by a space
      while (isspace((unsigned char)*key))
        key++;
      
      if (key == val || *key == '\0')
        goto next_part;
    }
    
    smisk_url_decode(key, val ? val - key : strlen(key));
    
    if (val) { // have a value
      *val++ = '\0'; // '=' -> '\0'
      int val_len = smisk_url_decode(val, strlen(val));
      if (!(py_val = PyString_FromStringAndSize(val, val_len))) {
        status = -1;
        break;
      }
      
      if (charset && (smisk_str_to_unicode(&py_val, charset, "strict") == -1)) {
        Py_DECREF(py_val);
        status = -1;
        break;
      }
    }
    else {
      py_val = Py_None;
      Py_INCREF(Py_None);
    }
    
    // Key
    if ( (py_key = PyString_FromString(key)) == NULL) {
      Py_DECREF(py_val);
      status = -1;
      break;
    }
    
    if (charset) {
      // As we might use the dictionary for keyword args, which need to be str and not unicode,
      // we normalize encoding to utf-8.
      if (smisk_str_recode(&py_key, charset, SMISK_KEY_CHARSET, "replace") == -1) {
        Py_DECREF(py_key);
        Py_DECREF(py_val);
        status = -1;
        break;
      }
    }
    
    assert(PyString_Check(py_key) == 1);
    assert(PyUnicode_Check(py_val) == 1);
    
    if ((status = PyDict_assoc_val_with_key(dict, py_val, py_key)) != 0)
      break;
    
    Py_DECREF(py_key);
    Py_DECREF(py_val);
    
next_part:
    key = strtok_r(NULL, separator, &strtok_ctx);
  } // end while (var)

  free(scpy);
  
  return status;
}


size_t smisk_stream_readline(char *str, int n, FCGX_Stream *stream) {
  int c;
  char *p = str;
  
  n--;
  
  EXTERN_OP_START;
  
  while (n > 0) {
    c = FCGX_GetChar(stream);
    if (c == EOF) {
      if (p == str) {
        EXTERN_OP_END;
        return 0;
      }
      else
        break;
    }
    *p++ = (char) c;
    n--;
    if (c == '\n')
      break;
  }
  
  EXTERN_OP_END;
  
  *p = '\0';
  return p-str;
}


void smisk_frepr_bytes(FILE *f, const char *s, size_t len) {
  int c;
  EXTERN_OP_START;
  fprintf(f, "bytes(%lu) '", (unsigned long int)len);
  while (len--) {
    c = *s++;
    if ( isgraph((unsigned char)c) || (c == ' ') ) {
      fputc(c, f);
    }
    else {
      fprintf(f, "\\x%02x", (unsigned char)c);
    }
  }
  fprintf(f, "'\n");
  EXTERN_OP_END;
}


double smisk_microtime(void) {
  struct timeval tp;
  if (gettimeofday(&tp, NULL) == 0) {
    return ((double)tp.tv_usec / 1000000.0) + tp.tv_sec;
  }
  return 0.0;
}


char smisk_size_unit (double *bytes) {
  if (*bytes > 1024000000.0) {
    *bytes = *bytes/1024000000.0;
    return 'G';
  }
  else if (*bytes > 1024000.0) {
    *bytes = *bytes/1024000.0;
    return 'M';
  }
  else if (*bytes > 1024.0) {
    *bytes = *bytes/1024.0;
    return 'K';
  }
  else {
    return 'B';
  }
}


static char binconvtab[] = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_-";
// Highest character                       f               v                               -
// Tokens                               16 chrs         32 chrs                         64 chrs
// Bits                                 4 bits          5 bits                          6 bits
//

char *smisk_encode_bin(const byte *in, size_t inlen, char *out, char nbits) {
  byte *p, *q;
  unsigned short w;
  int mask;
  int have;
  
  assert(nbits < 7);
  
  p = (byte *)in;
  q = p + inlen;
  
  w = 0;
  have = 0;
  mask = (1 << nbits) - 1;
  
  while (1) {
    if (have < nbits) {
      if (p < q) {
        w |= *p++ << have;
        have += 8;
      } else {
        /* consumed everything? */
        if (have == 0) break;
        /* No? We need a final round */
        have = nbits;
      }
    }
    
    /* consume nbits */
    *out++ = binconvtab[w & mask];
    w >>= nbits;
    have -= nbits;
  }
  
  *out = '\0';
  return out;
}


PyObject *smisk_util_pack (const byte *data, size_t size, int nbits) {
  PyObject *return_str;
  switch(nbits) {
    case 6:
      return_str = PyString_FromStringAndSize(NULL, 27);
      break;
    case 5:
      return_str = PyString_FromStringAndSize(NULL, 32);
      break;
    case 4:
      return_str = PyString_FromStringAndSize(NULL, 40);
      break;
    default:
      return PyErr_Format(PyExc_ValueError, "Invalid number of bits: %d", nbits);
  }
  smisk_encode_bin(data, size, PyString_AS_STRING(return_str), nbits);
  return return_str;
}


PyObject *smisk_find_string_by_prefix_in_dict(PyObject *list, PyObject *prefix) {
  Py_ssize_t num_items, prefix_len, item_len, i, x;
  char *item_ptr, *prefix_ptr, *prefix_it;
  PyObject *item;
  
  if (list == NULL)
    return PyErr_Format(PyExc_TypeError, "smisk_find_string_by_prefix_in_dict() called with list=NULL");
  
  if (!prefix || !SMISK_PyString_Check(prefix))
    return PyErr_Format(PyExc_TypeError, "first argument must be a string");
  
  num_items = PyList_GET_SIZE(list);
  prefix_len = PyString_Size(prefix);
  prefix_ptr = PyString_AsString(prefix);
  
  // Iterate over headers
  for (i=0; i<num_items; i++) {
    if ( (item = PyList_GET_ITEM(list, i)) && SMISK_PyString_Check(item) ) {
      item_len = PyString_Size(item);
      if (item_len < prefix_len)
        continue;
      item_ptr = PyString_AsString(item);
      prefix_it = prefix_ptr;
      
      for (x = 0; x < prefix_len; x++) {
        if ( toupper(*(prefix_it++)) != toupper(*(item_ptr++)) ) {
          prefix_it = NULL;
          break; // try next header...
        }
      }
      if (prefix_it)
        return PyInt_FromLong((long)i);
    }
  }
  
  return PyInt_FromLong(-1L);
}


int probably_call(float probability, probably_call_cb *cb, void *cb_arg) {
  int rc = 0;
  static float rand_max_f = (float)RAND_MAX;
  
  struct timeval tv;
  gettimeofday(&tv, NULL);
  srandom(tv.tv_usec);
  
  if ( ((float)random()) / rand_max_f < probability )
    rc = cb(cb_arg);
  
  return rc;
}


long smisk_object_hash(PyObject *obj) {
  PyObject *x;
  long h = PyObject_Hash(obj);
  if (h == -1) {
    // A little trick
    log_debug("smisk_object_hash: calculating hash by marshalling");
    PyErr_Clear();
    x = PyMarshal_WriteObjectToString(obj, Py_MARSHAL_VERSION);
    h = PyObject_Hash(x);
    Py_DECREF(x);
  }
  return h;
}


int smisk_str_recode( PyObject **str,
                             const char *src_charset,
                             const char *dst_charset,
                             const char *errors ) {
  // Does not modify recount on str
  PyObject *u, *s, *orig_str;
  
  if (strcmp(src_charset, dst_charset) == 0)
    return 0;
  
  u = PyUnicode_FromEncodedObject(*str, src_charset, errors);
  if (!u)
    return -1;
  
  s = PyUnicode_AsEncodedString(u, dst_charset, errors);
  Py_DECREF(u);
  if (!s)
    return -1;
  orig_str = *str;
  *str = s;
  Py_DECREF(orig_str);
  
  return 0;
}


int smisk_str_to_unicode( PyObject **str, const char *charset, const char *errors ) {
  // Decrements str and returns new reference to new unicode object.
  PyObject *u, *orig_str;
  
  u = PyUnicode_FromEncodedObject(*str, charset, errors);
  if (!u)
    return -1;
  orig_str = *str;
  *str = u;
  Py_DECREF(orig_str);
  
  return 0;
}
