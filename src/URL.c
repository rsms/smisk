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
#include "URL.h"
#include "atoin.h"
#include "utils.h"
#include <structmember.h>

#pragma mark Private C

/* Table of "reserved" and "unsafe" characters.  Those terms are
   rfc1738-speak, as such largely obsoleted by rfc2396 and later
   specs, but the general idea remains.

   A reserved character is the one that you can't decode without
   changing the meaning of the URL.  For example, you can't decode
   "/foo/%2f/bar" into "/foo///bar" because the number and contents of
   path components is different.  Non-reserved characters can be
   changed, so "/foo/%78/bar" is safe to change to "/foo/x/bar".  The
   unsafe characters are loosely based on rfc1738, plus "$" and ",",
   as recommended by rfc2396, and minus "~", which is very frequently
   used (and sometimes unrecognized as %7E by broken servers).

   An unsafe character is the one that should be encoded when URLs are
   placed in foreign environments.  E.g. space and newline are unsafe
   in HTTP contexts because HTTP uses them as separator and line
   terminator, so they must be encoded to %20 and %0A respectively.
   "*" is unsafe in shell context, etc.

   We determine whether a character is unsafe through static table
   lookup.  This code assumes ASCII character set and 8-bit chars.  */

enum {
  /* rfc1738 reserved chars + "$" and ",".  */
  urlchr_reserved = 1,

  /* rfc1738 unsafe chars, plus non-printables.  */
  urlchr_unsafe   = 2
};

#define urlchr_test(c, mask) (urlchr_table[(unsigned char)(c)] & (mask))
#define URL_RESERVED_CHAR(c) urlchr_test(c, urlchr_reserved)
#define URL_UNSAFE_CHAR(c) urlchr_test(c, urlchr_unsafe)

/* Shorthands for the table: */
#define R  urlchr_reserved
#define U  urlchr_unsafe
#define RU R|U

static const unsigned char urlchr_table[256] =
{
  U,  U,  U,  U,   U,  U,  U,  U,   /* NUL SOH STX ETX  EOT ENQ ACK BEL */
  U,  U,  U,  U,   U,  U,  U,  U,   /* BS  HT  LF  VT   FF  CR  SO  SI  */
  U,  U,  U,  U,   U,  U,  U,  U,   /* DLE DC1 DC2 DC3  DC4 NAK SYN ETB */
  U,  U,  U,  U,   U,  U,  U,  U,   /* CAN EM  SUB ESC  FS  GS  RS  US  */
  U,  0,  U, RU,   R,  U,  R,  0,   /* SP  !   "   #    $   %   &   '   */
  0,  0,  0,  R,   R,  0,  0,  R,   /* (   )   *   +    ,   -   .   /   */
  0,  0,  0,  0,   0,  0,  0,  0,   /* 0   1   2   3    4   5   6   7   */
  0,  0, RU,  R,   U,  R,  U,  R,   /* 8   9   :   ;    <   =   >   ?   */
 RU,  0,  0,  0,   0,  0,  0,  0,   /* @   A   B   C    D   E   F   G   */
  0,  0,  0,  0,   0,  0,  0,  0,   /* H   I   J   K    L   M   N   O   */
  0,  0,  0,  0,   0,  0,  0,  0,   /* P   Q   R   S    T   U   V   W   */
  0,  0,  0, RU,   U, RU,  U,  0,   /* X   Y   Z   [    \   ]   ^   _   */
  U,  0,  0,  0,   0,  0,  0,  0,   /* `   a   b   c    d   e   f   g   */
  0,  0,  0,  0,   0,  0,  0,  0,   /* h   i   j   k    l   m   n   o   */
  0,  0,  0,  0,   0,  0,  0,  0,   /* p   q   r   s    t   u   v   w   */
  0,  0,  0,  U,   U,  U,  0,  U,   /* x   y   z   {    |   }   ~   DEL */

  U, U, U, U,  U, U, U, U,  U, U, U, U,  U, U, U, U,
  U, U, U, U,  U, U, U, U,  U, U, U, U,  U, U, U, U,
  U, U, U, U,  U, U, U, U,  U, U, U, U,  U, U, U, U,
  U, U, U, U,  U, U, U, U,  U, U, U, U,  U, U, U, U,

  U, U, U, U,  U, U, U, U,  U, U, U, U,  U, U, U, U,
  U, U, U, U,  U, U, U, U,  U, U, U, U,  U, U, U, U,
  U, U, U, U,  U, U, U, U,  U, U, U, U,  U, U, U, U,
  U, U, U, U,  U, U, U, U,  U, U, U, U,  U, U, U, U,
};
#undef R
#undef U
#undef RU


/* The core of url_escape_* functions.  Escapes the characters that
   match the provided mask in urlchr_table.*/

static void _url_encode (const char *s, char *newstr, unsigned char mask) {
  const char *p1;
  char *p2;
  
  p1 = s;
  p2 = newstr;
  
  while (*p1) {
    /* Quote the characters that match the test mask. */
    if (urlchr_test (*p1, mask)) {
      unsigned char c = *p1++;
      *p2++ = '%';
      *p2++ = XNUM_TO_DIGIT (c >> 4);
      *p2++ = XNUM_TO_DIGIT (c & 0xf);
    }
    else {
      *p2++ = *p1++;
    }
  }
  
  *p2 = '\0';
}


char *smisk_url_encode(const char *s, int full) {
  const char *p1;
  char *new_s;
  unsigned char mask = full ? urlchr_reserved|urlchr_unsafe : urlchr_unsafe;
  size_t len = strlen(s);
  size_t new_len = len;
  
  for (p1 = s; *p1; p1++) {
    if (urlchr_test(*p1, mask)) {
      new_len += 2;
    }
  }
  
  if(new_len == len) {
    return strdup(s);
  }
  else {
    new_s = (char *)malloc(new_len);
  }
  
  _url_encode(s, new_s, mask);
  return new_s;
}


// returns (new) length of str
size_t smisk_url_decode(char *str, size_t len) {
  char *dest = str;
  char *data = str;

  while (len--) {
    if (*data == '+') {
      *dest = ' ';
    }
    else if (*data == '%' && len >= 2 && isxdigit((int) *(data + 1)) && isxdigit((int) *(data + 2))) {
      *dest = (char) X2DIGITS_TO_NUM(*(data + 1), *(data + 2));
      data += 2;
      len -= 2;
    } else {
      *dest = *data;
    }
    data++;
    dest++;
  }
  *dest = '\0';
  return dest - str;
}


static PyObject* encode_or_escape(PyObject* self, PyObject* str, unsigned char mask) {
  char *orgstr, *newstr;
  Py_ssize_t orglen;
  Py_ssize_t newlen;
  PyObject* newstr_py;
  
  if((orgstr = PyString_AsString(str)) == NULL) {
    return NULL; // TypeError was raised
  }
  
  orglen = PyString_GET_SIZE(str);
  
  if(orglen < 1) {
    // Empty string
    Py_INCREF(str);
    return str;
  }
  
  newlen = orglen;
  
  // Check new length
  const char *p1;
  for (p1 = orgstr; *p1; p1++) {
    if (urlchr_test (*p1, mask)) {
      newlen += 2;  /* Two more characters (hex digits) */
    }
  }
  
  if(orglen == newlen) {
    // No need to encode - return original string
    Py_INCREF(str);
    return str;
  }
  
  // Initialize new PyString
  if((newstr_py = PyString_FromStringAndSize(NULL, newlen)) == NULL) {
    return NULL;
  }
  
  // Do the actual encoding
  newstr = PyString_AS_STRING(newstr_py);
  _url_encode(orgstr, newstr, mask);
  
  // Return new string
  return newstr_py;
}

static int _parse(smisk_URL* self, const char *s, size_t len) { // bool URL::set( const string &str )
  struct vec { int len; const void *ptr; };
  struct url { struct vec proto; struct vec user; struct vec pass;
               struct vec host;  struct vec port; struct vec uri; };

  //const char *s = str.c_str();
  //int len = strlen(s);
  struct url *u = (struct url *)malloc(sizeof(struct url));
  //smisk_URL* u = self; // XXX tmp aliasing

  register const char  *p, *e;
  struct vec    *v, nil = { 0, 0 };

  (void) memset(u, 0, sizeof(*u));

  /* Now, dispatch URI */
  for (p = s, e = s + len, v = &u->proto; p < e; p++) {
    switch (*p) {
    
    case ':':
      if (v == &u->proto) {
        if (&p[2] < e && p[1] == '/' && p[2] == '/') {
          p += 2;
          v = &u->user;
        } else {
          u->user = u->proto;
          u->proto = nil;
          v = &u->pass;
        }
      } else if (v == &u->user) {
        v = &u->pass;
      } else if (v == &u->host) {
        v = &u->port;
      } else if (v == &u->uri) {
        /* : is allowed in path or query */
        v->len++;
      } else {
        return (-1);
      }
      break;
    
    case '@':
      if (v == &u->proto) {
        u->user = u->proto;
        u->proto = nil;
        v = &u->host;
      } else if (v == &u->pass || v == &u->user) {
        v = &u->host;
      } else if (v == &u->uri) {
        /* @ is allowed in path or query */
        v->len++;
      } else {
        return (-1);
      }
      break;
    
    case '/':
      #define  SETURI()  v = &u->uri; v->ptr = p; v->len = 1
      if ((v == &u->proto && u->proto.len == 0) ||
        v == &u->host || v == &u->port) {
        SETURI();
      } else if (v == &u->user) {
        u->host = u->user;
        u->user = nil;
        SETURI();
      } else if (v == &u->pass) {
        u->host = u->user;
        u->port = u->pass;
        u->user = u->pass = nil;
        SETURI();
      } else if (v == &u->uri) {
        /* / is allowed in path or query */
        v->len++;
      } else {
        return (-1);
      }
      break;
    
    default:
      if (!v->ptr)
        v->ptr = p;
      v->len++;
    }
  }

  if (v == &u->proto && v->len > 0) {
    v = ((char *) v->ptr)[0] == '/' ? &u->uri : &u->host;
    *v = u->proto;
    u->proto = nil;
  } else if (v == &u->user) {
    u->host = u->user;
    u->user = nil;
  } else if (v == &u->pass) {
    u->host = u->user;
    u->port = u->pass;
    u->user = u->pass = nil;
  }

  if((p - s) == -1)
    return 0;
  
  // Now, transfer valid parts to the URL instance
  self->scheme = Py_None;
  self->user = Py_None;
  self->password = Py_None;
  self->host = Py_None;
  self->port = 0;
  self->path = Py_None;
  self->query = Py_None;
  self->fragment = Py_None;
  
  if( u->proto.len )
    self->scheme = PyString_FromStringAndSize((char*)u->proto.ptr, u->proto.len);

  if( u->user.len )
    self->user = PyString_FromStringAndSize((char*)u->user.ptr, u->user.len);

  if( u->pass.len )
    self->password = PyString_FromStringAndSize((char*)u->pass.ptr, u->pass.len);

  if( u->host.len )
    self->host = PyString_FromStringAndSize((char*)u->host.ptr, u->host.len);

  if( u->port.len ) {
    self->port = atoin((char*)u->port.ptr, u->port.len);
    if(self->port < 0)
      self->port = -self->port;
  }
  if( u->uri.len ) {
    // Find query and frag parts
    void *q_start = memchr(u->uri.ptr, '?', u->uri.len);
    void *f_start = memchr(u->uri.ptr, '#', u->uri.len);
    
    // Both qery and frag
    if( (q_start != NULL) && (f_start != NULL) ) {
      // Really both q & f? (The ? comes before the #)
      if( q_start < f_start ) {
        self->path = PyString_FromStringAndSize((char*)u->uri.ptr, q_start - u->uri.ptr);
        self->query = PyString_FromStringAndSize((char*)q_start+1,  f_start - q_start -1);
        self->fragment = PyString_FromStringAndSize((char*)f_start+1, u->uri.len - (f_start - u->uri.ptr) -1);
      }
      // Only frag, but with a ? somewhere in it
      else {
        self->path = PyString_FromStringAndSize((char*)u->uri.ptr, f_start - u->uri.ptr);
        self->fragment = PyString_FromStringAndSize((char*)f_start+1, u->uri.len - (f_start - u->uri.ptr) -1);
      }
    }
    // Only query
    else if( q_start != NULL ) {
      self->path = PyString_FromStringAndSize((char*)u->uri.ptr, q_start - u->uri.ptr);
      self->query = PyString_FromStringAndSize((char*)q_start+1,  u->uri.len - (q_start - u->uri.ptr) -1);
    }
    // Only frag
    else if( f_start != NULL ) {
      self->path = PyString_FromStringAndSize((char*)u->uri.ptr, f_start - u->uri.ptr);
      self->fragment = PyString_FromStringAndSize((char*)f_start+1,  u->uri.len - (f_start - u->uri.ptr) -1);
    }
    // Neither query nor frag
    else {
      self->path = PyString_FromStringAndSize((char*)u->uri.ptr, u->uri.len);
    }
  }
  
  if(self->scheme == Py_None) Py_INCREF(self->scheme);
  if(self->user == Py_None) Py_INCREF(self->user);
  if(self->password == Py_None) Py_INCREF(self->password);
  if(self->host == Py_None) Py_INCREF(self->host);
  if(self->path == Py_None) Py_INCREF(self->path);
  if(self->query == Py_None) Py_INCREF(self->query);
  if(self->fragment == Py_None) Py_INCREF(self->fragment);

  free(u);
  return 1;
}


#pragma mark Initialization & deallocation


static PyObject * smisk_URL_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {
  log_debug("ENTER smisk_URL_new");
  smisk_URL *self;
  
  self = (smisk_URL *)type->tp_alloc(type, 0);
  if (self != NULL) {
    self->scheme    = Py_None; Py_INCREF(Py_None);
    self->user      = Py_None; Py_INCREF(Py_None);
    self->password  = Py_None; Py_INCREF(Py_None);
    self->host      = Py_None; Py_INCREF(Py_None);
    self->port      = 0;
    self->path      = Py_None; Py_INCREF(Py_None);
    self->query     = Py_None; Py_INCREF(Py_None);
    self->fragment  = Py_None; Py_INCREF(Py_None);
  }
  
  return (PyObject *)self;
}


int smisk_URL_init(smisk_URL* self, PyObject* args, PyObject* kwargs) {
  log_debug("ENTER smisk_URL_init");
  PyObject* str;
  
  // No arguments? (new empty url)
  if( (args == NULL) || (PyTuple_GET_SIZE(args) == 0) ) {
    return 0;
  }
  
  // Save reference to first argument (a string) and type check it
  str = PyTuple_GET_ITEM(args, 0);
  if(!PyString_Check(str)) {
    Py_DECREF(self);
    return -1;
  }
  
  if(!_parse(self, PyString_AS_STRING(str), PyString_GET_SIZE(str))) {
    PyErr_Format(PyExc_ValueError, "Failed to parse URL");
    Py_DECREF(self);
    return -1;
  }
  
  return 0;
}

void smisk_URL_dealloc(smisk_URL* self) {
  log_debug("ENTER smisk_URL_dealloc");
  Py_DECREF(self->scheme);
  Py_DECREF(self->user);
  Py_DECREF(self->password);
  Py_DECREF(self->host);
  Py_DECREF(self->path);
  Py_DECREF(self->query);
  Py_DECREF(self->fragment);
}


#pragma mark -
#pragma mark Methods


PyDoc_STRVAR(smisk_URL_encode_DOC,
  "Encode any unsafe or reserved characters in a given string for "
    "use in URI and URL contexts.\n"
  "\n"
  "The difference between encode and escape is that this function "
    "encodes characters like / and : which are considered safe for "
    "rendering url's, but not for using as a component in path, query "
    "or the fragment.\n"
  "\n"
  "In other words: Use encode() for path, query and fragment "
    "components. Use escape() on whole URLs for safe rendering in "
    "other contexts.\n"
  "\n"
  "Characters being escaped: $&+,/;=?<>\"#%{}|\\^~[]`@:\n"
  "Also low and high characters (< 33 || > 126) is encoded.\n"
  "\n"
  ":param  str:\n"
  ":type   str: string\n"
  ":rtype: string\n"
  ":raises TypeError: if str is not a string");
PyObject* smisk_URL_encode(PyObject* self, PyObject* str) {
  return encode_or_escape(self, str, urlchr_reserved|urlchr_unsafe);
}


PyDoc_STRVAR(smisk_URL_escape_DOC,
  "Escape unsafe characters ( <>\"#%{}|\\^~[]`@:\\033) in a given "
    "string for use in URI and URL contexts.\n"
  "\n"
  "See documentation of `encode()` to find out what the difference between "
    "escape() and encode() is.\n"
  "\n"
  ":param  str:\n"
  ":type   str: string\n"
  ":rtype: string\n"
  ":raises TypeError: if str is not a string");
PyObject* smisk_URL_escape(PyObject* self, PyObject* str) {
  return encode_or_escape(self, str, urlchr_unsafe);
}


PyDoc_STRVAR(smisk_URL_decode_DOC,
  "Restore data previously encoded by `encode()` or `escape()`.\n"
  "\n"
  "Done by transforming the sequences \"%HH\" to the character "
  "represented by the hexadecimal digits HH.\n"
  "\n"
  ":param  str:\n"
  ":type   str: string\n"
  ":rtype: string\n"
  ":raises TypeError: if str is not a string");
PyObject* smisk_URL_decode(PyObject* self, PyObject* str) {
  char *orgstr;
  Py_ssize_t orglen, newlen;
  register PyStringObject *newstr_py;
  
  if((orgstr = PyString_AsString(str)) == NULL) {
    return NULL; // TypeError raised
  }
  
  orglen = PyString_GET_SIZE(str);
  if(orglen < 1) {
    // Empty string
    Py_INCREF(str);
    return str;
  }
  
  // Initialize new PyString
  if((newstr_py = (PyStringObject *)PyString_FromStringAndSize(orgstr, orglen)) == NULL) {
    return NULL;
  }
  
  newlen = smisk_url_decode(PyString_AS_STRING(newstr_py), orglen);
  
  if(orglen == newlen) {
    // Did not need decoding
    Py_DECREF(newstr_py);
    Py_INCREF(str);
    return str;
  }
  
  // XXX This may be a problem in future Python versions as it's internal
  newstr_py->ob_size = newlen;
  
  // Return decoded string
  return (PyObject *)newstr_py;
}

PyDoc_STRVAR(smisk_URL_unescape_DOC,
  "Alias of `decode()`.\n"
  "\n"
  ":param  str:\n"
  ":type   str: string\n"
  ":rtype: string\n"
  ":raises TypeError: if str is not a string");

PyObject *smisk_URL___str__(smisk_URL* self) {
  PyObject *s = PyString_FromStringAndSize("",0);
  if(self->scheme != Py_None) {
    PyString_Concat(&s, self->scheme);
    PyString_Concat(&s, PyString_FromStringAndSize("://", 3));
  }
  if((self->user != Py_None) || (self->password != Py_None)) {
    if(self->user != Py_None) {
      PyString_Concat(&s, self->user);
    }
    if(self->password != Py_None) {
      PyString_Concat(&s, PyString_FromStringAndSize(":", 1));
      PyString_Concat(&s, self->password);
    }
    PyString_Concat(&s, PyString_FromStringAndSize("@", 1));
  }
  if(self->host != Py_None) {
    PyString_Concat(&s, self->host);
  }
  if(self->port > 0 && self->port != 80) { // should we really skip 80?
    PyString_Concat(&s, PyString_FromFormat(":%d", self->port));
  }
  if(self->path != Py_None) {
    PyString_Concat(&s, self->path);
  }
  if(self->query != Py_None) {
    PyString_Concat(&s, PyString_FromStringAndSize("?", 1));
    PyString_Concat(&s, self->query);
  }
  if(self->fragment != Py_None) {
    PyString_Concat(&s, PyString_FromStringAndSize("#", 1));
    PyString_Concat(&s, self->fragment);
  }
  
  return s;
}

#pragma mark -
#pragma mark Type construction

PyDoc_STRVAR(smisk_URL_DOC,
  "Uniform Resource Locator");

// Methods
static PyMethodDef smisk_URL_methods[] = {
  // Static methods
  {"encode", (PyCFunction)smisk_URL_encode,   METH_STATIC|METH_O, smisk_URL_encode_DOC},
  {"escape", (PyCFunction)smisk_URL_escape,   METH_STATIC|METH_O, smisk_URL_escape_DOC},
  {"decode", (PyCFunction)smisk_URL_decode,   METH_STATIC|METH_O, smisk_URL_decode_DOC},
  {"unescape", (PyCFunction)smisk_URL_decode, METH_STATIC|METH_O, smisk_URL_unescape_DOC},
  {NULL}
};

// Class Members
static struct PyMemberDef smisk_URL_members[] = {
  {"scheme",    T_OBJECT_EX, offsetof(smisk_URL, scheme),   RO, ":type: string"},
  {"user",      T_OBJECT_EX, offsetof(smisk_URL, user),     RO, ":type: string"},
  {"password",  T_OBJECT_EX, offsetof(smisk_URL, password), RO, ":type: string"},
  {"host",      T_OBJECT_EX, offsetof(smisk_URL, host),     RO, ":type: string"},
  {"port",      T_UINT,      offsetof(smisk_URL, port),     RO, ":type: uint"},
  {"path",      T_OBJECT_EX, offsetof(smisk_URL, path),     RO, ":type: string"},
  {"query",     T_OBJECT_EX, offsetof(smisk_URL, query),    RO, ":type: string"},
  {"fragment",  T_OBJECT_EX, offsetof(smisk_URL, fragment), RO, ":type: string"},
  {NULL}
};

// Type definition
PyTypeObject smisk_URLType = {
  PyObject_HEAD_INIT(&PyType_Type)
  0,                         /*ob_size*/
  "smisk.core.URL",             /*tp_name*/
  sizeof(smisk_URL),       /*tp_basicsize*/
  0,                         /*tp_itemsize*/
  (destructor)smisk_URL_dealloc,        /* tp_dealloc */
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
  (reprfunc)smisk_URL___str__,         /*tp_str*/
  0,                         /*tp_getattro*/
  0,                         /*tp_setattro*/
  0,                         /*tp_as_buffer*/
  Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE, /*tp_flags*/
  smisk_URL_DOC,          /*tp_doc*/
  (traverseproc)0,           /* tp_traverse */
  0,                         /* tp_clear */
  0,                         /* tp_richcompare */
  0,                         /* tp_weaklistoffset */
  0,                         /* tp_iter */
  0,                         /* tp_iternext */
  smisk_URL_methods,           /* tp_methods */
  smisk_URL_members,           /* tp_members */
  0,                           /* tp_getset */
  0,                           /* tp_base */
  0,                           /* tp_dict */
  0,                           /* tp_descr_get */
  0,                           /* tp_descr_set */
  0,                           /* tp_dictoffset */
  (initproc)smisk_URL_init, /* tp_init */
  0,                           /* tp_alloc */
  smisk_URL_new,           /* tp_new */
  0                            /* tp_free */
};

int smisk_URL_register_types(PyObject *module) {
  if(PyType_Ready(&smisk_URLType) == 0) {
    return PyModule_AddObject(module, "URL", (PyObject *)&smisk_URLType);
  }
  return -1;
}
