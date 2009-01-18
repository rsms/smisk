/*
Copyright (c) 2007-2009, Rasmus Andersson

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

#define URLCHR_TEST(c, mask) (urlchr_table[(unsigned char)(c)] & (mask))
#define URL_RESERVED_CHAR(c) URLCHR_TEST(c, urlchr_reserved)
#define URL_UNSAFE_CHAR(c) URLCHR_TEST(c, urlchr_unsafe)

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

static void _url_encode (const char *s, size_t length, char *newstr, int mask) {
  const char *p1;
  char *p2;
  
  p1 = s;
  p2 = newstr;
  
  while (length--) {
    /* Quote the characters that match the test mask. */
    if (URLCHR_TEST(*p1, mask)) {
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


char *smisk_url_encode(const char *s, size_t length, int full) {
  const char *p1;
  char *new_s;
  int mask = full ? urlchr_reserved|urlchr_unsafe : urlchr_unsafe;
  size_t new_len = length;
  
  for (p1 = s; *p1; p1++) {
    if (URLCHR_TEST(*p1, mask))
      new_len += 2;
  }
  
  if (new_len == length)
    return strdup(s);
  else
    new_s = (char *)malloc(new_len);
  
  _url_encode(s, length, new_s, mask);
  return new_s;
}


// returns (new) length of str
size_t smisk_url_decode(char *str, size_t length) {
  char *dest = str;
  char *data = str;

  while (length--) {
    if (*data == '+') {
      *dest = ' ';
    }
    else if (*data == '%'
      && length >= 2
      && isxdigit((unsigned char) *(data + 1)) 
      && isxdigit((unsigned char) *(data + 2)))
    {
      *dest = (char) X2DIGITS_TO_NUM(*(data + 1), *(data + 2));
      data += 2;
      length -= 2;
    }
    else {
      *dest = *data;
    }
    data++;
    dest++;
  }
  *dest = '\0';
  return dest - str;
}


static PyObject *encode_or_escape(PyObject *self, PyObject *str, int mask) {
  log_trace("ENTER");
  char *orgstr, *newstr;
  Py_ssize_t orglen, newlen;
  PyObject *newstr_py, *unicode_str = NULL;
  
  if (!SMISK_STRING_CHECK(str)) {
    PyErr_SetString(PyExc_TypeError, "first argument must be a string");
    return NULL;
  }
  
  orglen = PyString_Size(str);
  
  if (orglen < 1) {
    Py_INCREF(str);
    return str;
  }
  
  if (PyUnicode_Check(str)) {
    unicode_str = str;
    str = PyUnicode_AsUTF8String(str);
    if (str == NULL)
      return NULL;
  }
  
  if ((orgstr = PyBytes_AS_STRING(str)) == NULL)
    return NULL;
  
  newlen = orglen;
  
  // Check new length
  const char *p1;
  for (p1 = orgstr; *p1; p1++) {
    if (URLCHR_TEST(*p1, mask))
      newlen += 2;  /* Two more characters (hex digits) */
  }
  
  if (orglen == newlen) {
    // No need to encode - return original string
    if (unicode_str) {
      Py_DECREF(str);
      str = unicode_str;
    }
    Py_INCREF(str);
    return str;
  }
  
  // Initialize new PyString
  if ((newstr_py = PyBytes_FromStringAndSize(NULL, newlen)) == NULL)
    return NULL;
  
  // Do the actual encoding
  newstr = PyBytes_AS_STRING(newstr_py);
  _url_encode(orgstr, orglen, newstr, mask);
  
  if (unicode_str) {
    Py_DECREF(str); // release utf8 intermediate copy
    str = newstr_py;
    newstr_py = PyUnicode_DecodeUTF8(newstr, newlen, "strict");
    Py_DECREF(str); // release intermediate newstr_py created in PyBytes_FromStringAndSize
  }
  
  // Return new string
  return newstr_py;
}


static int _parse(smisk_URL* self, const char *s, ssize_t len) {
  struct vec { ssize_t len; const void *ptr; };
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
        }
        else {
          u->user = u->proto;
          u->proto = nil;
          v = &u->pass;
        }
      }
      else if (v == &u->user) {
        v = &u->pass;
      }
      else if (v == &u->host) {
        v = &u->port;
      }
      else if (v == &u->uri) {
        /* : is allowed in path or query */
        v->len++;
      }
      else {
        return -1;
      }
      break;
    
    case '@':
      if (v == &u->proto) {
        u->user = u->proto;
        u->proto = nil;
        v = &u->host;
      }
      else if (v == &u->pass || v == &u->user) {
        v = &u->host;
      }
      else if (v == &u->uri) {
        /* @ is allowed in path or query */
        v->len++;
      }
      else {
        return -1;
      }
      break;
    
    case '/':
      #define  SETURI()  v = &u->uri; v->ptr = p; v->len = 1
      if ((v == &u->proto && u->proto.len == 0) ||
        v == &u->host || v == &u->port) {
        SETURI();
      }
      else if (v == &u->user) {
        u->host = u->user;
        u->user = nil;
        SETURI();
      }
      else if (v == &u->pass) {
        u->host = u->user;
        u->port = u->pass;
        u->user = u->pass = nil;
        SETURI();
      }
      else if (v == &u->uri) {
        /* / is allowed in path or query */
        v->len++;
      }
      else {
        return -1;
      }
      break;
    
    default:
      if (!v->ptr)
        v->ptr = p;
      v->len++;
    }
  }

  if (v == &u->proto && v->len > 0) {
    v = ( ((char *)v->ptr)[0] == '/' ) ? &u->uri : &u->host;
    *v = u->proto;
    u->proto = nil;
  }
  else if (v == &u->user) {
    u->host = u->user;
    u->user = nil;
  }
  else if (v == &u->pass) {
    u->host = u->user;
    u->port = u->pass;
    u->user = u->pass = nil;
  }

  if ((p - s) == -1)
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
  
  if ( u->proto.len ) {
    self->scheme = smisk_PyBytes_FromStringAndSize_lower(u->proto.ptr, (Py_ssize_t)u->proto.len);
    if (self->scheme == NULL)
      return -1;
  }

  if ( u->user.len ) {
    self->user = PyBytes_FromStringAndSize((char*)u->user.ptr, u->user.len);
    if (self->user == NULL)
      return -1;
  }

  if ( u->pass.len ) {
    self->password = PyBytes_FromStringAndSize((char*)u->pass.ptr, u->pass.len);
    if (self->password == NULL)
      return -1;
  }

  if ( u->host.len ) {
    self->host = PyBytes_FromStringAndSize((char*)u->host.ptr, u->host.len);
    if (self->host == NULL)
      return -1;
  }

  if ( u->port.len ) {
    self->port = atoin((char*)u->port.ptr, (size_t)u->port.len);
    if (self->port < 0)
      self->port = -self->port;
  }
  if ( u->uri.len ) {
    // Find query and frag parts
    void *q_start = memchr(u->uri.ptr, '?', (size_t)u->uri.len);
    void *f_start = memchr(u->uri.ptr, '#', (size_t)u->uri.len);
    
    // Both qery and frag
    if ( (q_start != NULL) && (f_start != NULL) ) {
      // Really both q & f? (The ? comes before the #)
      if ( q_start < f_start ) {
        self->path = PyBytes_FromStringAndSize((char*)u->uri.ptr, q_start - u->uri.ptr);
        self->query = PyBytes_FromStringAndSize((char*)q_start+1,  f_start - q_start -1);
        self->fragment = PyBytes_FromStringAndSize((char*)f_start+1, u->uri.len - (f_start - u->uri.ptr) -1);
      }
      // Only frag, but with a ? somewhere in it
      else {
        self->path = PyBytes_FromStringAndSize((char*)u->uri.ptr, f_start - u->uri.ptr);
        self->fragment = PyBytes_FromStringAndSize((char*)f_start+1, u->uri.len - (f_start - u->uri.ptr) -1);
      }
    }
    // Only query
    else if ( q_start != NULL ) {
      self->path = PyBytes_FromStringAndSize((char*)u->uri.ptr, q_start - u->uri.ptr);
      self->query = PyBytes_FromStringAndSize((char*)q_start+1,  u->uri.len - (q_start - u->uri.ptr) -1);
    }
    // Only frag
    else if ( f_start != NULL ) {
      self->path = PyBytes_FromStringAndSize((char*)u->uri.ptr, f_start - u->uri.ptr);
      self->fragment = PyBytes_FromStringAndSize((char*)f_start+1,  u->uri.len - (f_start - u->uri.ptr) -1);
    }
    // Neither query nor frag
    else {
      self->path = PyBytes_FromStringAndSize((char*)u->uri.ptr, u->uri.len);
    }
  }
  
  if (self->scheme == Py_None) Py_INCREF(self->scheme);
  if (self->user == Py_None) Py_INCREF(self->user);
  if (self->password == Py_None) Py_INCREF(self->password);
  if (self->host == Py_None) Py_INCREF(self->host);
  if (self->path == Py_None) Py_INCREF(self->path);
  if (self->query == Py_None) Py_INCREF(self->query);
  if (self->fragment == Py_None) Py_INCREF(self->fragment);

  free(u);
  return 1;
}


#pragma mark Initialization & deallocation


PyObject *smisk_URL_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {
  log_trace("ENTER");
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


int smisk_URL_init(smisk_URL *self, PyObject *args, PyObject *kwargs) {
  log_trace("ENTER");
  PyObject *str;
  
  // No arguments? (new empty url)
  if ( !args || (PyTuple_GET_SIZE(args) == 0) )
    return 0;
  
  // Save reference to first argument (a string) and type check it
  str = PyTuple_GET_ITEM(args, 0);
  
  if (!SMISK_STRING_CHECK(str)) {
    str = PyObject_Str(str);
    if (str == NULL)
      return -1;
  }
  else {
    Py_INCREF(str);
  }
  
  if (!_parse(self, PyString_AsString(str), PyString_Size(str))) {
    PyErr_SetString(PyExc_ValueError, "Failed to parse URL");
    Py_DECREF(str);
    Py_DECREF(self);
    return -1;
  }
  
  Py_DECREF(str);
  return 0;
}


void smisk_URL_dealloc(smisk_URL* self) {
  log_trace("ENTER");
  
  Py_DECREF(self->scheme);
  Py_DECREF(self->user);
  Py_DECREF(self->password);
  Py_DECREF(self->host);
  Py_DECREF(self->path);
  Py_DECREF(self->query);
  Py_DECREF(self->fragment);
  
  self->ob_type->tp_free((PyObject*)self);
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
PyObject *smisk_URL_encode(PyObject *self, PyObject *str) {
  log_trace("ENTER");
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
PyObject *smisk_URL_escape(PyObject *self, PyObject *str) {
  log_trace("ENTER");
  return encode_or_escape(self, str, urlchr_unsafe);
}


PyDoc_STRVAR(smisk_URL_unescape_DOC,
  "Alias of `decode()`.\n"
  "\n"
  ":param  str:\n"
  ":type   str: string\n"
  ":rtype: string\n"
  ":raises TypeError: if str is not a string");

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
PyObject *smisk_URL_decode(PyObject *self, PyObject *str) {
  log_trace("ENTER");
  char *orgstr, *newstr;
  Py_ssize_t orglen, newlen;
  register PyStringObject *newstr_py;
  PyObject *unicode_str = NULL;
  
  if (!SMISK_STRING_CHECK(str)) {
    PyErr_SetString(PyExc_TypeError, "first argument must be a string");
    return NULL;
  }
  
  if (PyUnicode_Check(str)) {
    unicode_str = str;
    str = PyUnicode_AsUTF8String(str);
    if (str == NULL)
      return NULL;
  }
  
  if ((orgstr = PyBytes_AS_STRING(str)) == NULL)
    return NULL;
  
  orglen = PyBytes_GET_SIZE(str);
  if (orglen < 1) {
    // Empty string
    if (unicode_str) {
      Py_DECREF(str);
      str = unicode_str;
    }
    Py_INCREF(str);
    return str;
  }
  
  // Initialize new PyString
  if ((newstr_py = (PyStringObject *)PyBytes_FromStringAndSize(orgstr, orglen)) == NULL)
    return NULL;
  
  newstr = PyBytes_AS_STRING(newstr_py);
  
  newlen = smisk_url_decode(newstr, (size_t)orglen);
  
  if (orglen == newlen) {
    // Did not need decoding
    Py_DECREF(newstr_py);
    if (unicode_str) {
      Py_DECREF(str);
      str = unicode_str;
    }
    Py_INCREF(str);
    return str;
  }
  
  if (unicode_str) {
    // release utf8 intermediate copy
    Py_DECREF(str);
    
    // Return decoded unicode string
    unicode_str = PyUnicode_DecodeUTF8(newstr, newlen, "strict");
    
    // Release intermediate newstr_py created in PyBytes_FromStringAndSize.
    Py_DECREF(newstr_py);
    
    // Return decoded unicode string
    return unicode_str;
  }
  else {
    // Warning: This may be a problem in future Python versions as it's internal
    newstr_py->ob_size = newlen;
    
    // Return decoded string
    return (PyObject *)newstr_py;
  }
}


PyDoc_STRVAR(smisk_URL_decompose_query_DOC,
  "Parses a query string into a dictionary.\n"
  "\n"
  ":param  string:\n"
  ":type   string: str\n"
  ":param  charset: 'utf-8' by default. None to disable.\n"
  ":type   charset: str\n"
  ":rtype: string (str or unicode)\n"
  ":raises TypeError: if str is not a string\n"
  ":see:   `Request.get`\n"
  ":see:   `Request.post`");
PyObject *smisk_URL_decompose_query(PyObject *nothing, PyObject *args, PyObject *kwargs) {
  log_trace("ENTER");
  
  PyObject *string = NULL;
  const char *charset = NULL;
  static char *kwlist[] = { "string", "charset", NULL };
  if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O|s", kwlist, &string, &charset))
    return NULL;
  
  char *s;
  PyObject *d;
  
  if (!PyBytes_Check(string)) {
    string = PyObject_Str(string);
    if (string == NULL)
      return NULL;
  }
  else {
    Py_INCREF(string);
  }
  
  if ((s = PyString_AsString(string)) == NULL) {
    Py_DECREF(string);
    return NULL; // TypeError raised
  }
  
  if ((d = PyDict_New()) == NULL) {
    Py_DECREF(string);
    return NULL;
  }
  
  if (smisk_parse_input_data(s, "&", 0, d, charset) != 0) {
    Py_DECREF(string);
    Py_DECREF(d);
    return NULL;
  }
  
  Py_DECREF(string);
  
  return d;
}


PyDoc_STRVAR(smisk_URL_to_str_DOC,
  "Alias of `to_s()`.\n"
  "\n"
  ":param  scheme:\n"
  ":param  user:\n"
  ":param  password:\n"
  ":param  host:\n"
  ":param  port:\n"
  ":param  path:\n"
  ":param  query:\n"
  ":param  fragment:\n"
  ":type   scheme:    bool\n"
  ":type   user:      bool\n"
  ":type   password:  bool\n"
  ":type   host:      bool\n"
  ":type   port:      bool\n"
  ":type   path:      bool\n"
  ":type   query:     bool\n"
  ":type   fragment:  bool\n"
  ":rtype: string");
PyDoc_STRVAR(smisk_URL_to_s_DOC,
  "String representation.\n"
  "\n"
  "By passing ``False`` for any of the arguments, you can omit certain parts from being included in the string produced. This can come in handy when for example you want to sanitize away password or maybe not include any path, query or fragment.\n"
  "\n"
  ":param  scheme:\n"
  ":param  user:\n"
  ":param  password:\n"
  ":param  host:\n"
  ":param  port:\n"
  ":param  port80:\n"
  ":param  path:\n"
  ":param  query:\n"
  ":param  fragment:\n"
  ":type   scheme:    bool\n"
  ":type   user:      bool\n"
  ":type   password:  bool\n"
  ":type   host:      bool\n"
  ":type   port:      bool\n"
  ":type   port80:    bool\n"
  ":type   path:      bool\n"
  ":type   query:     bool\n"
  ":type   fragment:  bool\n"
  ":rtype: string");
PyObject *smisk_URL_to_s(smisk_URL* self, PyObject *args, PyObject *kwargs) {
  log_trace("ENTER");
  PyObject *scheme, *user, *password, *host, *port, *port80, *path, *query, *fragment;
  PyObject *one;
  static char *kwlist[] = {
  "scheme","user","password","host","port","port80","path","query","fragment", NULL};
   scheme = user = password = host = port = port80 = path = query = fragment = NULL;
  if (args && kwargs && ! PyArg_ParseTupleAndKeywords(args, kwargs, "|OOOOOOOOO", kwlist,
      &scheme, &user, &password, &host, &port, &port80, &path, &query, &fragment))
    return NULL;
  
  one = NUMBER_FromLong(1);
  
  // DRY -- otherwise kittens will be wasted.
  #define ENABLED(x) ( self->x != Py_None && (x == NULL || x == Py_True || x == one) )
  
  PyObject *s = PyBytes_FromStringAndSize("", 0);
  
  if (ENABLED(scheme)) {
    PyString_Concat(&s, self->scheme);
    PyString_ConcatAndDel(&s, PyBytes_FromStringAndSize("://", 3));
  }
  
  if (ENABLED(user)) {
    PyString_Concat(&s, self->user);
    if (ENABLED(password)) {
      PyString_ConcatAndDel(&s, PyBytes_FromStringAndSize(":", 1));
      PyString_Concat(&s, self->password);
    }
    PyString_ConcatAndDel(&s, PyBytes_FromStringAndSize("@", 1));
  }
  
  if (ENABLED(host))
    PyString_Concat(&s, self->host);
  
  // port is an int, so we can't use our pretty ENABLED macro here
  if ( (port == NULL || port == Py_True || port == one) && (self->port > 0) ) {
    if (self->port != 80 || (port80 == Py_True || port80 == one) )
      PyString_ConcatAndDel(&s, PyString_FromFormat(":%d", self->port));
  }
  
  if (ENABLED(path))
    PyString_Concat(&s, self->path);
  
  if (ENABLED(query) && self->query != Py_None && PyString_Size(self->query) > 0) {
    PyString_ConcatAndDel(&s, PyBytes_FromStringAndSize("?", 1));
    PyString_Concat(&s, self->query);
  }
  
  if (ENABLED(fragment) && self->fragment != Py_None) {
    PyString_ConcatAndDel(&s, PyBytes_FromStringAndSize("#", 1));
    PyString_Concat(&s, self->fragment);
  }
  
  #undef ENABLED
  
  Py_DECREF(one);
  return s;
}


PyObject *smisk_URL_get_uri(smisk_URL* self) {
  log_trace("ENTER");
  
  PyObject *s = self->path;
  Py_INCREF(s); // this is the callers reference eventually.
  
  if (self->query != Py_None && PyString_Size(self->query) > 0) {
    PyString_ConcatAndDel(&s, PyBytes_FromStringAndSize("?", 1));
    PyString_Concat(&s, self->query);
  }
  
  if (self->fragment != Py_None) {
    PyString_ConcatAndDel(&s, PyBytes_FromStringAndSize("#", 1));
    PyString_Concat(&s, self->fragment);
  }
  
  return s;
}


// XXX: missing documentation
PyObject *smisk_URL___str__(smisk_URL* self) {
  log_trace("ENTER");
  return smisk_URL_to_s(self, NULL, NULL);
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
  {"decompose_query", (PyCFunction)smisk_URL_decompose_query, METH_STATIC|METH_VARARGS|METH_KEYWORDS, 
    smisk_URL_decompose_query_DOC},
  
  // Instance methods
  {"to_s",    (PyCFunction)smisk_URL_to_s,    METH_VARARGS|METH_KEYWORDS, smisk_URL_to_s_DOC},
  {"to_str",  (PyCFunction)smisk_URL_to_s,    METH_VARARGS|METH_KEYWORDS, smisk_URL_to_str_DOC}, // alias of to_s
  
  {NULL, NULL, 0, NULL}
};

// Properties
static PyGetSetDef smisk_URL_getset[] = {
  {"uri", (getter)smisk_URL_get_uri, (setter)0, NULL, NULL},
  {NULL, NULL, NULL, NULL, NULL}
};

// Class Members
static struct PyMemberDef smisk_URL_members[] = {
  {"scheme",    T_OBJECT_EX, offsetof(smisk_URL, scheme),   0, ":type: string"},
  {"user",      T_OBJECT_EX, offsetof(smisk_URL, user),     0, ":type: string"},
  {"password",  T_OBJECT_EX, offsetof(smisk_URL, password), 0, ":type: string"},
  {"host",      T_OBJECT_EX, offsetof(smisk_URL, host),     0, ":type: string"},
  {"port",      T_UINT,      offsetof(smisk_URL, port),     0, ":type: uint"},
  {"path",      T_OBJECT_EX, offsetof(smisk_URL, path),     0, ":type: string"},
  {"query",     T_OBJECT_EX, offsetof(smisk_URL, query),    0, ":type: string"},
  {"fragment",  T_OBJECT_EX, offsetof(smisk_URL, fragment), 0, ":type: string"},
  {NULL, 0, 0, 0, NULL}
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
  (reprfunc)smisk_URL___str__,  /*tp_str*/
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
  smisk_URL_getset,            /* tp_getset */
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
  log_trace("ENTER");
  if (PyType_Ready(&smisk_URLType) == 0)
    return PyModule_AddObject(module, "URL", (PyObject *)&smisk_URLType);
  return -1;
}
