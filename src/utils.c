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

#include <Python.h>
#include <stdlib.h>
#include <time.h>
#include "module.h"


// Returns PyStringObject (borrowed reference)
PyObject* format_exc(void)
{
  PyObject* msg;
  PyObject* lines;
  PyObject* traceback;
  PyObject* format_exception;
  PyObject *type = NULL, *value = NULL, *tb = NULL;
  
  PyErr_Fetch(&type, &value, &tb);
  PyErr_Clear();
  if(type == NULL) {
    DLog("No error occured. type == NULL");
    Py_RETURN_NONE;
  }
  
  if( (traceback = PyImport_ImportModule("traceback")) == NULL ) {
    DLog("PyImport_ImportModule('traceback') == NULL");
    return NULL;
  }
  
  if( (format_exception = PyObject_GetAttrString(traceback, "format_exception")) == NULL ) {
    DLog("PyObject_GetAttrString(traceback, 'format_exception') == NULL");
    Py_DECREF(traceback);
    return NULL;
  }
  
  if(value == NULL) {
    DLog("value == NULL");
    value = Py_None;
    Py_INCREF(value);
  }
  
  if(tb == NULL) {
    DLog("tb == NULL");
    tb = Py_None;
    Py_INCREF(tb);
  }
  
  if( (lines = PyObject_CallFunctionObjArgs(format_exception, type, value, tb, NULL)) == NULL ) {
    DLog("PyObject_CallFunctionObjArgs(format_exception...) == NULL");
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
      DLog("msg == NULL");
      Py_DECREF(lines);
      return NULL;
    }
  }
  
  Py_INCREF(msg);
  return msg;
}


char *strndup(const char *s, size_t len) {
  char *p;
  if((p = (char *)malloc(len+1)) == NULL) {
    return p;
  }
  memcpy(p, s, len);
  p[len] = 0;
  return p;
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



int parse_input_data(char *s, const char *separator, int is_cookie_data, PyObject *dict) {
  char *res = NULL, *key, *val, *strtok_ctx = NULL;
  int free_buffer = 0, status = 0;
  
  res = strdup(s);
  free_buffer = 1;
  
  key = strtok_r(res, separator, &strtok_ctx);
  
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
      *val++ = '\0';
      int val_len = smisk_url_decode(val, strlen(val));
      py_val = PyString_FromStringAndSize(val, val_len);
    } else {
      py_val = Py_None;
    }
    // save
    py_key = PyString_FromString(key);
    if(PyDict_Contains(dict, py_key)) {
      // multi-value
      PyObject *existing_val = PyDict_GetItem(dict, py_key);
      if(PyList_CheckExact(existing_val)) {
        // just append
        if(PyList_Append(existing_val, py_val) != 0) {
          status = -1;
          break;
        }
      }
      else {
        // convert to list
        PyObject *new_val = PyList_New(2);
        PyList_SET_ITEM(new_val, 0, existing_val);
        PyList_SET_ITEM(new_val, 1, py_val);
        if(PyDict_SetItem(dict, py_key, new_val) != 0) {
          status = -1;
          break;
        }
      }
    }
    else { // key is unique as far as we know
      if(PyDict_SetItem(dict, py_key, py_val) != 0) {
        status = -1;
        break;
      }
    }
    
next_cookie:
    key = strtok_r(NULL, separator, &strtok_ctx);
  } // end while(var)

  if (free_buffer) {
    free(res);
  }
  
  return status;
}

