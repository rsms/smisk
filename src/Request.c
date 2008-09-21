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
#include "__init__.h"
#include "utils.h"
#include "multipart.h"
#include "file.h"
#include "uid.h"
#include "Request.h"
#include "Response.h"
#include "Application.h"
#include "SessionStore.h"

#include <unistd.h>
#include <structmember.h>
#include <fastcgi.h>

#pragma mark Internal


static char *smisk_read_fcgxstream(FCGX_Stream *stream, long length) {
  char *s;
  int bytes_read;
  
  if (length == 0) {
    return strdup("");
  }
  else if (length > 0) {
    s = (char *)malloc(length+1);
    EXTERN_OP(bytes_read = FCGX_GetStr(s, length, stream));
    s[(bytes_read < length) ? bytes_read : length] = '\0';
    return s;
  }
  else { // unknown length
    size_t size = SMISK_STREAM_READ_CHUNKSIZE;
    s = (char *)malloc(size+1);
    
    while (1) {
      EXTERN_OP(bytes_read = FCGX_GetStr(s, SMISK_STREAM_READ_CHUNKSIZE, stream));
      if (bytes_read < SMISK_STREAM_READ_CHUNKSIZE) {
        s[(size - SMISK_STREAM_READ_CHUNKSIZE) + bytes_read] = '\0';
        break; // EOF
      }
      size += SMISK_STREAM_READ_CHUNKSIZE;
      s = (char *)realloc(s, size+1);
    }
    
    return s;
  }
}


static int _parse_request_body(smisk_Request* self) {
  char *content_type;
  long content_length;
  int rc;
  
  if ((self->post = PyDict_New()) == NULL)
    return -1;
  
  if ((self->files = PyDict_New()) == NULL)
    return -1;
  
  if ((content_type = FCGX_GetParam("CONTENT_TYPE", self->envp))) {
    // Parse content-length if available
    char *t = FCGX_GetParam("CONTENT_LENGTH", self->envp);
    content_length = (t != NULL) ? atol(t) : -1;
    
    if (strstr(content_type, "multipart/")) {
      rc = smisk_multipart_parse_stream(self->input->stream, content_length, 
                                        self->post, self->files);
      if (rc != 0)
        return -1;
    }
    else if (strstr(content_type, "/x-www-form-urlencoded")) {
      // Todo: Optimize: keep s buffer and reuse it between calls.
      char *s = smisk_read_fcgxstream(self->input->stream, content_length);
      int parse_status = smisk_parse_input_data(s, "&", 0, self->post);
      free(s);
      
      if (parse_status != 0)
        return -1;
    }
    // else, leave it as raw input
  }
  
  return 0;
}


// This should only be used internally and for strings we are certain
// only contain characters within ASCII.
inline char *_strtolower(char *s) {
  char *p = s;
  do {
    *p = tolower(*p);
  } while ( *p++ );
  return s;
}


static inline int _valid_sid(const char *uid, size_t len) {
  size_t i;
  for (i=0;i<len;i++) {
    if ( ((uid[i] < '0') || (uid[i] > '9')) 
#if (SMISK_SESSION_NBITS == 6)
      &&((uid[i] < 'a') || (uid[i] > 'f')) 
      &&((uid[i] < 'A') || (uid[i] > 'F'))
      &&(uid[i] != '+')
      &&(uid[i] != '/')
#elif (SMISK_SESSION_NBITS == 5)
      &&((uid[i] < 'a') || (uid[i] > 'v'))
#else
      &&((uid[i] < 'a') || (uid[i] > 'f'))
#endif
      )
    {
      return 0;
    }
  }
  return 1;
}


static PyObject *_generate_sid(smisk_Request* self) {
  smisk_uid_t uid;
  char *node;
  
  if ((node = FCGX_GetParam("REMOTE_ADDR", self->envp)) == NULL)
    node = "SID";
  
  if (smisk_uid_create(&uid, node, strlen(node)) == -1) {
    PyErr_SetString(PyExc_SystemError, "smisk_uid_create() failed");
    return NULL;
  }
  
  return smisk_uid_format(&uid, SMISK_SESSION_NBITS);
}


static int _cleanup_session(smisk_Request* self) {
  log_trace("ENTER");
  // Write modified session
  if (self->session_id) {
    long h = 0;
    
    log_debug("self->session_id = %s", self->session_id ? PyString_AS_STRING(self->session_id) : "NULL");
    log_debug("self->session = %p", self->session);
    log_debug("self->initial_session_hash = %lu", self->initial_session_hash);
    log_debug("PyObject_Hash(self->session) = %lu", self->session ? PyObject_Hash(self->session) : 0);
    assert(self->session);
    
    if (smisk_require_app() != 0)
      return -1;
    
    ENSURE_BY_GETTER(smisk_current_app->sessions, smisk_Application_get_sessions(smisk_current_app),
      return -1;
    );
    
    if ( ((self->initial_session_hash == 0) && (self->session != Py_None)) 
      || (self->initial_session_hash != (h = PyObject_Hash(self->session))) )
    {
      // Session data was changed. Write it.
      DUMP_REFCOUNT(self->session);
      DUMP_REFCOUNT(self->session_id);
      if (PyObject_CallMethod(smisk_current_app->sessions, "write", "OO", self->session_id, self->session) == NULL) {
        log_debug("sessions.write() returned NULL");
        return -1;
      }
    }
    else if (self->initial_session_hash == h) {
      // Session data was unchanged. Give the session store the opportunity to refresh this sessions' TTL:
      if (PyObject_CallMethod(smisk_current_app->sessions, "refresh", "O", self->session_id) == NULL)
        return -1;
    }
    
  }
  return 0;
}


static int _cleanup_uploads(smisk_Request* self) {
  log_trace("ENTER");
  // Delete unused uploaded files
  int st = 0;
  if (self->files) {
    EXTERN_OP_START;
    PyObject *files = PyDict_Values(self->files);
    size_t i, count = PyList_GET_SIZE(files);
    for (i=0;i<count;i++) {
      PyObject *file = PyList_GET_ITEM(files, i);
      if (file != Py_None) {
        PyObject *path = PyDict_GetItemString(file, "path");
        if (path) {
          char *fn = PyString_AsString(path);
          log_debug("Trying to unlink file '%s' (%s)", 
            fn, smisk_file_exist(fn) ? "exists" : "not found - skipping");
          if (smisk_file_exist(fn) && (unlink(fn) != 0)) {
            log_debug("Failed to unlink temporary file %s", fn);
            PyErr_SetFromErrnoWithFilename(PyExc_IOError, __FILE__);
            st = -1;
          }
          IFDEBUG(else {
            log_debug("Unlinked unused uploaded file '%s'", fn);
          });
        }
      }
    }
    EXTERN_OP_END;
    Py_DECREF(files);
  }
  return st;
}


// Called by Application.run just after a successful accept() 
// and just before calling service(). Also called when server stops.
int smisk_Request_reset (smisk_Request* self) {
  log_trace("ENTER");
  
  if (_cleanup_session(self) != 0)
    return -1;
  
  if (_cleanup_uploads(self) != 0)
    return -1;
  
  Py_CLEAR(self->env);
  Py_CLEAR(self->url);
  Py_CLEAR(self->get);
  Py_CLEAR(self->post);
  Py_CLEAR(self->files);
  Py_CLEAR(self->cookies);
  Py_CLEAR(self->session);
  Py_CLEAR(self->session_id);
  
  self->initial_session_hash = 0;
  
  return 0;
}


#pragma mark -
#pragma mark Initialization & deallocation


PyObject * smisk_Request_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {
  log_trace("ENTER");
  smisk_Request *self;
  
  self = (smisk_Request *)type->tp_alloc(type, 0);
  if (self != NULL) {
    if (smisk_Request_reset(self) != 0) {
      Py_DECREF(self);
      return NULL;
    }
  
    // Construct a new Stream for in
    self->input = (smisk_Stream*)smisk_Stream_new(&smisk_StreamType, NULL, NULL);
    if (self->input == NULL) {
      Py_DECREF(self);
      return NULL;
    }
  
    // Construct a new Stream for err
    self->errors = (smisk_Stream*)smisk_Stream_new(&smisk_StreamType, NULL, NULL);
    if (self->errors == NULL) {
      Py_DECREF(self);
      return NULL;
    }
  }
  
  return (PyObject *)self;
}


int smisk_Request_init(smisk_Request* self, PyObject *args, PyObject *kwargs) {
  log_trace("ENTER");
  return 0;
}


void smisk_Request_dealloc(smisk_Request* self) {
  log_trace("ENTER");
  
  smisk_Request_reset(self);
  
  Py_XDECREF(self->input);
  Py_XDECREF(self->errors);
  
  if (self->envp_buf)
    free(self->envp_buf);
  
  self->ob_type->tp_free((PyObject*)self);
}


#pragma mark -
#pragma mark Methods


PyDoc_STRVAR(smisk_Request_log_error_DOC,
  "Log something through `errors` including process name and id.\n"
  "\n"
  "Normally, `errors` ends up in the host server error log.\n"
  "\n"
  ":param  message: Message\n"
  ":type   message: string\n"
  ":raises `IOError`:\n"
  ":rtype: None");
PyObject *smisk_Request_log_error(smisk_Request* self, PyObject *msg) {
  log_trace("ENTER");
  
  int rc;
  static const char format[] = "%s[%d] %s";
  
  if (!self->errors->stream || ((PyObject *)self->errors->stream == Py_None)) {
    PyErr_SetString(smisk_IOError, "request.errors stream not initialized. Only makes sense during an active request.");
    return NULL;
  }
  
  if (!msg || !PyString_Check(msg)) {
    PyErr_SetString(PyExc_TypeError, "first argument must be a string");
    return NULL;
  }
  
  EXTERN_OP( rc = FCGX_FPrintF(self->errors->stream, format, Py_GetProgramName(), 
                               getpid(), PyString_AsString(msg)) );
  if (rc == -1) {
    EXTERN_OP(fprintf(stderr, format, Py_GetProgramName(), getpid(), PyString_AsString(msg)));
    return PyErr_SET_FROM_ERRNO;
  }
  
  Py_RETURN_NONE;
}


PyObject *smisk_Request_is_active(smisk_Request* self) {
  log_trace("ENTER");
  PyObject *b = self->env ? Py_True : Py_False;
  Py_INCREF(b);
  return b;
}


PyObject *smisk_Request_get_env(smisk_Request* self) {
  log_trace("ENTER");
  //log_debug("ENTER smisk_Request_get_env");
  static PyObject *_cached_SERVER_SOFTWARE_k = NULL;
  static PyObject *_cached_SERVER_SOFTWARE_v = NULL;
  
  // Lazy initializer
  if (self->env == NULL) {
    
    // Alloc new dict
    self->env = PyDict_New();
    if (self->env == NULL) {
      log_debug("self->env == NULL");
      return NULL;
    }
    
    // Transcribe envp to dict
    if (self->envp != NULL) {
      
      PyObject *k, *v;
      char **envp = self->envp;
      
      // Parse env into dict
      for ( ; *envp; envp++) {
        
        char *value = strchr(*envp, '=');
        
        if (!value) {
          log_debug("Strange item in ENV (missing '=')");
          continue;
        }
        
        // SERVER_SOFTWARE will most likely not change during the process lifetime,
        // or at least, we done really care, so lets cache it.
        if (smisk_str8cmp(*envp, 'S','E','R','V','E','R','_','S') &&
          (*envp)[8]=='O'  && (*envp)[9]=='F'  && (*envp)[10]=='T' && (*envp)[11]=='W' && 
          (*envp)[12]=='A' && (*envp)[13]=='R' && (*envp)[14]=='E')
        {
          
          if (_cached_SERVER_SOFTWARE_k == NULL) {
            
            k = PyString_FromStringAndSize(*envp, value-*envp);
            if (k) PyString_InternInPlace(&k);
            if (k == NULL)
              return NULL;
            
            v = PyString_FromFormat("%s smisk/%s", ++value, SMISK_VERSION);
            if (v == NULL) {
              Py_DECREF(k);
              return NULL;
            }
            
            _cached_SERVER_SOFTWARE_k = k;
            _cached_SERVER_SOFTWARE_v = v;
            
          }
          
          if ( PyDict_SetItem(self->env, _cached_SERVER_SOFTWARE_k, _cached_SERVER_SOFTWARE_v) != 0 )
            return NULL;
          
          continue;
        }
        
        k = PyString_FromStringAndSize(*envp, value-*envp);
        if (k) PyString_InternInPlace(&k);
        if (k == NULL)
          return NULL;
        
        v = PyString_InternFromString(++value);
        if (v == NULL) {
          Py_DECREF(k);
          return NULL;
        }
        
        if ( PyDict_SetItem(self->env, (PyObject *)k, (PyObject *)v) != 0 )
          return NULL;
        
        // Release ownership
        assert_refcount(k, > 1);
        assert_refcount(v, > 1);
        Py_DECREF(k);
        Py_DECREF(v);
      }
    }
  }
  
  Py_INCREF(self->env);
  return (PyObject*)self->env;
}


PyObject *smisk_Request_get_url(smisk_Request* self) {
  log_trace("ENTER");
  char *s, *p, *s2;
  PyObject *old;
  
  if (self->url == NULL) {
    if ( (self->url = (smisk_URL *)smisk_URL_new(&smisk_URLType, NULL, NULL)) == NULL )
      return NULL;
    
    // Scheme
    if ((s = FCGX_GetParam("SERVER_PROTOCOL", self->envp))) {
      old = self->url->scheme;
      
      // As this is called MANY times, this op is really worth it...
      if ( ((s[0]=='H')&&(s[1]=='T')&&(s[2]=='T')&&(s[3]=='P')) 
        ||((s[0]=='h')&&(s[1]=='t')&&(s[2]=='t')&&(s[3]=='p')) ) {
        if ( (s[4]=='S'||s[4]=='s') ) { // what about if the interface spec is less than 5 chars?
          self->url->scheme = kString_https;
          Py_INCREF(kString_https);
        }
        else {
          self->url->scheme = kString_http;
          Py_INCREF(kString_http);
        }
      }
      else {
        Py_ssize_t len = strlen(s); 
        if ((p = strchr(s, '/')))
          len = (Py_ssize_t)(p-s);
        self->url->scheme = PyString_FromStringAndSize(_strtolower(s), len);
      }
      
      Py_CLEAR(old);
    }
    
    // User
    if ((s = FCGX_GetParam("REMOTE_USER", self->envp))) {
      old = self->url->user;
      self->url->user = PyString_FromString(s);
      Py_CLEAR(old);
    }
    
    // Host & port
    s = FCGX_GetParam("SERVER_NAME", self->envp);
    old = self->url->host;
    if ((p = strchr(s, ':'))) {
      self->url->host = PyString_FromStringAndSize(s, p-s);
      self->url->port = atoi(p+1);
    }
    else if ((s2 = FCGX_GetParam("SERVER_PORT", self->envp))) {
      self->url->host = PyString_FromString(s);
      self->url->port = atoi(s2);
    }
    else {
      self->url->host = PyString_FromString(s);
    }
    PyString_InternInPlace(&self->url->host);
    if (self->url->host == NULL)
      return PyErr_NoMemory();
    Py_CLEAR(old);
    
    // Path & querystring
    // Not in RFC, but considered standard
    if ((s = FCGX_GetParam("REQUEST_URI", self->envp))) {
      if ((p = strchr(s, '?'))) {
        *p = '\0';
        
        old = self->url->path;
        self->url->path = PyString_FromString(s);
        Py_DECREF(old);
        
        old = self->url->query;
        self->url->query = PyString_FromString(p+1);
        Py_DECREF(old);
      }
      else {
        old = self->url->path;
        self->url->path = PyString_FromString(s);
        Py_DECREF(old);
      }
    }
    // Non-REQUEST_URI compliant fallback
    else {
      if ((s = FCGX_GetParam("SCRIPT_NAME", self->envp))) {
        old = self->url->path;
        self->url->path = PyString_FromString(s);
        Py_DECREF(old);
        // May not always give the same results as the above implementation
        // because the CGI specification does claim "This information should be
        // decoded by the server if it comes from a URL" which is a bit vauge.
        if ((s = FCGX_GetParam("PATH_INFO", self->envp)))
          PyString_ConcatAndDel(&self->url->path, PyString_FromString(s));
      }
      if ((s = FCGX_GetParam("QUERY_STRING", self->envp))) {
        old = self->url->query;
        self->url->query = PyString_FromString(s);
        Py_DECREF(old);
      }
    }
    
  }
  
  Py_INCREF(self->url);
  return (PyObject *)self->url;
}


PyObject *smisk_Request_get_get(smisk_Request* self) {
  log_trace("ENTER");
  if (self->get == NULL) {
    
    if ((self->get = PyDict_New()) == NULL)
      return NULL;
    
    ENSURE_BY_GETTER(self->url, smisk_Request_get_url(self),
      return NULL;
    );
    
    if (self->url->query && (self->url->query != Py_None) && (PyString_GET_SIZE(self->url->query) > 0)) {
      assert_refcount(self->get, == 1);
      if (smisk_parse_input_data(PyString_AS_STRING(self->url->query), "&", 0, self->get) != 0) {
        Py_DECREF(self->get);
        self->get = NULL;
        return NULL;
      }
    }
  }
  
  Py_INCREF(self->get);
  return self->get;
}


PyObject *smisk_Request_get_post(smisk_Request* self) {
  log_trace("ENTER");
  
  if ( (self->post == NULL) && ((_parse_request_body(self) != 0)) )
    return NULL;
  
  Py_INCREF(self->post); // callers reference
  return self->post;
}


PyObject *smisk_Request_get_files(smisk_Request* self) {
  log_trace("ENTER");
  
  if ( (self->files == NULL) && (_parse_request_body(self) != 0) )
    return NULL;
  
  Py_INCREF(self->files); // callers reference
  return self->files;
}


PyObject *smisk_Request_get_cookies(smisk_Request* self) {
  log_trace("ENTER");
  char *http_cookie;
  
  if (self->cookies == NULL) {
    
    if ((self->cookies = PyDict_New()) == NULL)
      return NULL;
    
    if ((http_cookie = FCGX_GetParam("HTTP_COOKIE", self->envp))) {
      log_debug("Parsing input data");
      if (smisk_parse_input_data(http_cookie, ";", 1, self->cookies) != 0) {
        Py_DECREF(self->cookies);
        self->cookies = NULL;
        return NULL;
      }
      log_debug("Done parsing input data");
    }
  }
  
  Py_INCREF(self->cookies); // callers reference
  return self->cookies;
}


static PyObject *smisk_Request_get_session_id(smisk_Request* self) {
  log_trace("ENTER");
  if (self->session_id == NULL) {
    
    if (smisk_require_app() != 0)
      return NULL;
    
    ENSURE_BY_GETTER(self->cookies, smisk_Request_get_cookies(self),
      return NULL;
    );
    
    ENSURE_BY_GETTER(smisk_current_app->sessions, smisk_Application_get_sessions(smisk_current_app),
      return NULL;
    );
    
    assert(self->session == NULL);
    
    // Has SID in cookie? - if so, validate
    self->session_id = PyDict_GetItem(self->cookies,
      ((smisk_SessionStore *)smisk_current_app->sessions)->name);
    if ( self->session_id != NULL ) {
      if (!PyString_Check(self->session_id)) {
        if (PyList_Check(self->session_id)) {
          log_debug("Ambiguous: Multiple SID supplied in request. Will use first one.");
          if ( (self->session_id = PyList_GetItem(self->session_id, 0)) == NULL ) {
            return NULL;
          }
          else if (!PyString_Check(self->session_id)) {
            PyErr_SetString(PyExc_TypeError, "self.session_id is not a string");
            self->session_id = NULL;
            return NULL;
          }
        }
        else {
          log_debug("Inconsistency error: Provided SID is neither a single nor multiple string value");
          PyErr_SetString(PyExc_TypeError, "type of self.session_id is neither string nor list");
          self->session_id = NULL;
          return NULL;
        }
      }
      log_debug("SID '%s' provided by request", PyString_AS_STRING(self->session_id));
      // As this is the first time we aquire the SID and it was provided by the user,
      // we will also read up the session to validate wherethere this SID is valid.
      if (!_valid_sid(PyString_AS_STRING(self->session_id), PyString_GET_SIZE(self->session_id))) {
        log_debug("Invalid SID provided by request (illegal format)");
        self->session_id = NULL;
      }
      else {
        self->session = PyObject_CallMethod(smisk_current_app->sessions, "read", "O", self->session_id);
        
        if (self->session == NULL) {
          if (PyErr_ExceptionMatches(smisk_InvalidSessionError)) {
            PyErr_Clear();
            log_debug("Invalid SID provided by request (no data)");
            self->session_id = NULL;
          }
          else {
            self->session_id = NULL; // Error
            return NULL;
          }
        }
        else {
          // Valid SID
          log_debug("Valid SID provided by request");
          Py_INCREF(self->session_id);
        }
      }
    }
    
    // No SID-cookie or incorrect SID?
    if (self->session_id == NULL) {
      assert(self->session == NULL);
      if ( (self->session_id = _generate_sid(self)) == NULL )
        return NULL;
      
      // We do not call sessions.read() here because we *know* there is no data available.
      self->session = Py_None;
      Py_INCREF(Py_None);
      self->initial_session_hash = 0;
      if (smisk_current_app->response->has_begun == Py_True) {
        PyErr_SetString(smisk_Error, "Output already started - too late to send session id with response");
        return NULL;
      }
    }
    else {
      assert(self->session != NULL);
      // Compute and save hash of loaded data
      self->initial_session_hash = PyObject_Hash(self->session);
      log_debug("self->initial_session_hash = %lu", self->initial_session_hash);
    }
    
    assert(self->session != NULL);
  }
  
  Py_INCREF(self->session_id); // callers reference
  return self->session_id;
}


static int smisk_Request_set_session_id(smisk_Request* self, PyObject *session_id) {
  log_trace("ENTER");
  
  if (smisk_current_app->response->has_begun == Py_True) {
    PyErr_SetString(smisk_Error, "Output already started - too late to set session id");
    return -1;
  }
  
  ENSURE_BY_GETTER(self->session_id, smisk_Request_get_session_id(self),
    return -1;
  );
  
  // Delete old session data (a copy of it is still in this apps memory)
  if (PyObject_CallMethod(smisk_current_app->sessions, "destroy", "O", self->session_id) == NULL)
    return -1;
  
  REPLACE_OBJ(self->session_id, session_id, PyObject);
  self->initial_session_hash = 0; // Causes "sessions.write()" and "Set-Cookie: SID="
  return self->session_id ? 0 : -1;
}


static PyObject *smisk_Request_get_session(smisk_Request* self) {
  log_trace("ENTER");
  if (self->session == NULL) {
    // get_session_id will take it from here
    ENSURE_BY_GETTER(self->session_id, smisk_Request_get_session_id(self),
      return NULL;
    );
  }
  Py_INCREF(self->session); // callers reference
  return self->session;
}


static int smisk_Request_set_session(smisk_Request* self, PyObject *val) {
  log_trace("ENTER val=%p", val);
  IFDEBUG(DUMP_REPR(val));
  
  ENSURE_BY_GETTER(self->session_id, smisk_Request_get_session_id(self),
    return -1;
  );
  
  // Passing None causes the current session to be destroyed
  if (val == Py_None) {
    if (self->session != Py_None) {
      log_debug("Destroying session '%s'", PyString_AS_STRING(self->session_id));
      assert(smisk_current_app);
      assert(smisk_current_app->sessions);
      
      if (PyObject_CallMethod(smisk_current_app->sessions, "destroy", "O", self->session_id) == NULL)
        return -1;
      
      self->initial_session_hash = 0;
      REPLACE_OBJ(self->session, Py_None, PyObject);
    }
    IFDEBUG(else {
      log_debug("No need to destroy - self.session == None");
    })
    return 0;
  }
  // else: actually set session
  log_debug("Setting self->session = val");
  REPLACE_OBJ(self->session, val, PyObject);
  return self->session ? 0 : -1;
}


#pragma mark -
#pragma mark Iteration


PyObject *smisk_Request___iter__(smisk_Request *self) {
  log_trace("ENTER");
  return Py_INCREF(self->input), (PyObject*)self->input;
}


#pragma mark -
#pragma mark Type construction


PyDoc_STRVAR(smisk_Request_DOC,
  "A HTTP request");

// Methods
static PyMethodDef smisk_Request_methods[] = {
  {"log_error", (PyCFunction)smisk_Request_log_error, METH_O, smisk_Request_log_error_DOC},
  {NULL, NULL, 0, NULL}
};

// Properties
static PyGetSetDef smisk_Request_getset[] = {
  {"env", (getter)smisk_Request_get_env,  (setter)0,
    ":type: dict\n\n"
    "HTTP transaction environment.", NULL},
  
  {"url", (getter)smisk_Request_get_url,  (setter)0,
    ":type: `URL`\n\n"
    "Reconstructed URL.", NULL},
  
  {"get", (getter)smisk_Request_get_get,  (setter)0,
    ":type: dict\n\n"
    "Parameters passed in the query string part of the URL.", NULL},
  
  {"post", (getter)smisk_Request_get_post, (setter)0,
    ":type: dict\n\n"
    "Parameters passed in the body of a POST request.", NULL},
  
  {"files", (getter)smisk_Request_get_files,  (setter)0,
    ":type: dict\n\n"
    "Any files uploaded via a POST request.", NULL},
  
  {"cookies", (getter)smisk_Request_get_cookies,  (setter)0,
    ":type: dict\n\n"
    "Any cookies that was attached to the request.", NULL},
  
  {"session", (getter)smisk_Request_get_session, (setter)smisk_Request_set_session,
    ":type: object\n\n"
    "Current session.\n"
    "\n"
    "Any modifications to the session must be done before output has begun, as it "
    "will add a ``Set-Cookie:`` header to the response.", NULL},
  
  {"session_id", (getter)smisk_Request_get_session_id, (setter)smisk_Request_set_session_id,
    ":type: string\n\n"
    "Current session id.", NULL},
  
  {"is_active", (getter)smisk_Request_is_active,  (setter)0, ":type: bool\n\n"
    "Indicates if the request is active, if we are in the middle of a "
    "*HTTP transaction*", NULL},
  
  {NULL, NULL, NULL, NULL, NULL}
};

// Class members
static struct PyMemberDef smisk_Request_members[] = {
  {"input", T_OBJECT_EX, offsetof(smisk_Request, input), RO,
    "Input stream.\n"
    "\n"
    "If you send any data which is neither ``x-www-form-urlencoded`` nor ``multipart`` "
    "format, you will be able to read the raw POST body from this stream.\n"
    "\n"
    "You could read ``x-www-form-urlencoded`` or ``multipart`` POST requests in raw "
    "format, but you have to read from this stream before calling any of `post` or "
    "`files`, since they will otherwise trigger the built-in parser and read all data "
    "from the stream.\n"
    "\n"
    "**Example of how to parse a JSON request:**\n"
    "\n"
    ".. python::\n"
    "\n"
    " import cjson as json\n"
    " import smisk\n"
    " class App(smisk.Application):\n"
    "   def service(self):\n"
    "     if self.request.env['REQUEST_METHOD'] == 'POST':\n"
    "       self.response.write(repr(json.decode(self.request.input.read())) + \"\\n\")\n"
    " \n"
    " App().run()\n"
    "\n"
    "You could then send a request using curl for example:\n"
    "\n"
    "``curl --data-binary '{\"Url\": \"http://www.example.com/image/481989943\", \"Position\": [125, \"100\"]}' http://localhost:8080/``\n"
    ":type: `Stream`\n"
    "\n"
    },
  
  {"errors",   T_OBJECT_EX, offsetof(smisk_Request, errors),   RO, ":type: `Stream`"},
  
  {NULL, 0, 0, 0, NULL}
};

// Type definition
PyTypeObject smisk_RequestType = {
  PyObject_HEAD_INIT(&PyType_Type)
  0,                         /*ob_size*/
  "smisk.core.Request",             /*tp_name*/
  sizeof(smisk_Request),       /*tp_basicsize*/
  0,                         /*tp_itemsize*/
  (destructor)smisk_Request_dealloc,        /* tp_dealloc */
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
  Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE, /*tp_flags*/
  smisk_Request_DOC,          /*tp_doc*/
  (traverseproc)0,           /* tp_traverse */
  0,                         /* tp_clear */
  0,                         /* tp_richcompare */
  0,                         /* tp_weaklistoffset */
  (getiterfunc)smisk_Request___iter__,  /* tp_iter -- Returns self->input which in turn has tp_iternext over readline */
  0,                         /* tp_iternext */
  smisk_Request_methods,      /* tp_methods */
  smisk_Request_members,      /* tp_members */
  smisk_Request_getset,         /* tp_getset */
  0,                           /* tp_base */
  0,                           /* tp_dict */
  0,                           /* tp_descr_get */
  0,                           /* tp_descr_set */
  0,                           /* tp_dictoffset */
  (initproc)smisk_Request_init, /* tp_init */
  0,                           /* tp_alloc */
  smisk_Request_new,           /* tp_new */
  0                            /* tp_free */
};

int smisk_Request_register_types(PyObject *module) {
  log_trace("ENTER");
  
  if (PyType_Ready(&smisk_RequestType) == 0)
    return PyModule_AddObject(module, "Request", (PyObject *)&smisk_RequestType);
  
  return -1;
}
