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

#include <fcgiapp.h>
#include <Python.h>
#include <stdlib.h>
#include <unistd.h>
#include <time.h>
#include "module.h"
#include "URL.h"


// Returns PyStringObject (borrowed reference)
PyObject* format_exc(void)
{
  PyObject* msg = NULL;
  PyObject* lines = NULL;
  PyObject* traceback = NULL;
  PyObject* format_exception = NULL;
  PyObject *type = NULL, *value = NULL, *tb = NULL;
  
  PyErr_Fetch(&type, &value, &tb);
  PyErr_Clear();
  if(type == NULL) {
    log_debug("No error occured. type == NULL");
    Py_RETURN_NONE;
  }
  
  if( (traceback = PyImport_ImportModule("traceback")) == NULL ) {
    log_debug("PyImport_ImportModule('traceback') == NULL");
    return NULL;
  }
  
  if( (format_exception = PyObject_GetAttrString(traceback, "format_exception")) == NULL ) {
    log_debug("PyObject_GetAttrString(traceback, 'format_exception') == NULL");
    Py_DECREF(traceback);
    return NULL;
  }
  
  if(value == NULL) {
    log_debug("value == NULL");
    value = Py_None;
    Py_INCREF(value);
  }
  
  if(tb == NULL) {
    log_debug("tb == NULL");
    tb = Py_None;
    Py_INCREF(tb);
  }
  
  if( (lines = PyObject_CallFunctionObjArgs(format_exception, type, value, tb, NULL)) == NULL ) {
    log_debug("PyObject_CallFunctionObjArgs(format_exception...) == NULL");
    Py_DECREF(format_exception);
    Py_DECREF(traceback);
    return NULL;
  }
  
  Py_DECREF(format_exception);
  Py_DECREF(traceback);
  
  msg = PyString_FromString("");
  Py_ssize_t i = 0, lines_len = PyList_GET_SIZE(lines);
  for(;i<lines_len;i++) {
    PyString_ConcatAndDel(&msg, PyList_GET_ITEM(lines, i));
    if(msg == NULL) {
      log_debug("msg == NULL");
      Py_DECREF(lines);
      return NULL;
    }
  }
  
  return msg;
}


char *timestr(struct tm *time_or_null) {
  if(!time_or_null) {
    time_t curtime = time(NULL);
    time_or_null = localtime(&curtime);
  }
  
  char *buffer = (char*)malloc(sizeof(char)*20);
  strftime(buffer, 20, "%Y-%m-%d %H:%M:%S", time_or_null);
  
  return buffer;
}


int PyDict_assoc_val_with_key(PyObject *dict, PyObject *val, PyObject* key) {
  PyObject *existing_val, *new_val;
  
  if(PyDict_Contains(dict, key)) {
    // multi-value
    existing_val = PyDict_GetItem(dict, key);
    
    if(PyList_CheckExact(existing_val)) {
      // just append
      if(PyList_Append(existing_val, val) != 0) {
        return -1;
      }
    }
    else {
      // convert to list
      new_val = PyList_New(2);
      PyList_SET_ITEM(new_val, 0, existing_val);
      PyList_SET_ITEM(new_val, 1, val);
      Py_INCREF(existing_val);
      Py_INCREF(val);
      if(PyDict_SetItem(dict, key, new_val) != 0) {
        return -1;
      }
      assert_refcount(new_val, == 2);
      Py_DECREF(new_val); // we don't own it anymore
    }
  }
  else { // key is unique as far as we know
    if(PyDict_SetItem(dict, key, val) != 0) {
      return -1;
    }
  }
  
  assert_refcount(val, > 1);
  return 0;
}


int parse_input_data(char *s, const char *separator, int is_cookie_data, PyObject *dict) {
  char *scpy, *key, *val, *strtok_ctx = NULL;
  int status = 0;
  
  log_debug("parse_input_data '%s'", s);
  scpy = strdup(s);
  key = strtok_r(scpy, separator, &strtok_ctx);
  
  while (key) {
    val = strchr(key, '=');
    
    if (is_cookie_data) {
      // Remove leading spaces from cookie names, needed for multi-cookie 
      // header where ; can be followed by a space
      while (isspace(*key)) {
        key++;
      }
      if (key == val || *key == '\0') {
        goto next_cookie;
      }
    }
    
    PyObject *py_key, *py_val;
    
    smisk_url_decode(key, strlen(key));
    
    if (val) { // have a value
      *val++ = '\0'; // '=' -> '\0'
      int val_len = smisk_url_decode(val, strlen(val));
      py_val = PyString_FromStringAndSize(val, val_len);
    } else {
      py_val = Py_None;
      Py_INCREF(Py_None);
    }
    
    // save
    py_key = PyString_FromString(key);
    if((status = PyDict_assoc_val_with_key(dict, py_val, py_key)) != 0) {
      break;
    }
    Py_DECREF(py_key);
    Py_DECREF(py_val);
    
next_cookie:
    key = strtok_r(NULL, separator, &strtok_ctx);
  } // end while(var)

  free(scpy);
  
  return status;
}


size_t smisk_stream_readline(char *str, int n, FCGX_Stream *stream) {
  int c;
  char *p = str;

  n--;
  while (n > 0) {
    c = FCGX_GetChar(stream);
    if(c == EOF) {
      if(p == str)
        return 0;
      else
        break;
    }
    *p++ = (char) c;
    n--;
    if(c == '\n')
      break;
  }
  *p = '\0';
  return p-str;
}


void frepr_bytes(FILE *f, const char *s, size_t len) {
  int c;
  fprintf(f, "bytes(%lu) '", len);
  while(len--) {
    c = *s++;
    if( isgraph(c) || (c == ' ') ) {
      fputc(c, f);
    }
    else {
      fprintf(f, "\\x%02x", (unsigned char)c);
    }
  }
  fprintf(f, "'\n");
}


int file_exist(const char *fn) {
  return ((access(fn, R_OK) == 0) ? 1 : 0);
}

