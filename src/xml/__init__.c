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
#include "../__init__.h"
#include "__init__.h"
#include "../utils.h"

#undef MOD_IDENT
#define MOD_IDENT "smisk.core.xml"

#define IS_RESERVED(c) (chr_table[(unsigned char)(c)])

PyObject *smisk_xml = NULL; // the module

#pragma mark C API only

static const unsigned char chr_table[256] = {
  0,  0,  0,  0,    0,  0,  0,  0,   /*    NUL SOH STX ETX   EOT ENQ ACK BEL   */
  0,  0,  0,  0,    0,  0,  0,  0,   /*    BS  HT  LF  VT    FF  CR  SO  SI    */
  0,  0,  0,  0,    0,  0,  0,  0,   /*    DLE DC1 DC2 DC3   DC4 NAK SYN ETB   */
  0,  0,  0,  0,    0,  0,  0,  0,   /*    CAN EM  SUB ESC   FS  GS  RS  US    */
  
  0,  0,  1,  0,    0,  0,  1,  0,   /*    SP  !   "   #     $   %   &   '     */
  0,  0,  0,  0,    0,  0,  0,  0,   /*    (   )   *   +     ,   -   .   /     */
  0,  0,  0,  0,    0,  0,  0,  0,   /*    0   1   2   3     4   5   6   7     */
  0,  0,  0,  0,    1,  0,  1,  0,   /*    8   9   :   ;     <   =   >   ?     */
  
  0,  0,  0,  0,    0,  0,  0,  0,   /*    @   A   B   C     D   E   F   G     */
  0,  0,  0,  0,    0,  0,  0,  0,   /*    H   I   J   K     L   M   N   O     */
  0,  0,  0,  0,    0,  0,  0,  0,   /*    P   Q   R   S     T   U   V   W     */
  0,  0,  0,  0,    0,  0,  0,  0,   /*    X   Y   Z   [     \   ]   ^   _     */
  
  0,  0,  0,  0,    0,  0,  0,  0,   /*    `   a   b   c     d   e   f   g     */
  0,  0,  0,  0,    0,  0,  0,  0,   /*    h   i   j   k     l   m   n   o     */
  0,  0,  0,  0,    0,  0,  0,  0,   /*    p   q   r   s     t   u   v   w     */
  0,  0,  0,  0,    0,  0,  0,  0,   /*    x   y   z   {     |   }   ~   DEL   */

  0, 0, 0, 0,  0, 0, 0, 0,  0, 0, 0, 0,  0, 0, 0, 0,
  0, 0, 0, 0,  0, 0, 0, 0,  0, 0, 0, 0,  0, 0, 0, 0,
  0, 0, 0, 0,  0, 0, 0, 0,  0, 0, 0, 0,  0, 0, 0, 0,
  0, 0, 0, 0,  0, 0, 0, 0,  0, 0, 0, 0,  0, 0, 0, 0,

  0, 0, 0, 0,  0, 0, 0, 0,  0, 0, 0, 0,  0, 0, 0, 0,
  0, 0, 0, 0,  0, 0, 0, 0,  0, 0, 0, 0,  0, 0, 0, 0,
  0, 0, 0, 0,  0, 0, 0, 0,  0, 0, 0, 0,  0, 0, 0, 0,
  0, 0, 0, 0,  0, 0, 0, 0,  0, 0, 0, 0,  0, 0, 0, 0
};

static const char* ent_table[63] = {
  NULL, NULL, NULL, NULL,   NULL, NULL, NULL, NULL, 
  NULL, NULL, NULL, NULL,   NULL, NULL, NULL, NULL, 
  NULL, NULL, NULL, NULL,   NULL, NULL, NULL, NULL, 
  NULL, NULL, NULL, NULL,   NULL, NULL, NULL, NULL, 
  
  NULL, NULL, "&quot;"/* " */, NULL,   NULL, NULL, "&amp;"/* & */, NULL, 
  NULL, NULL, NULL, NULL,   NULL, NULL, NULL, NULL, 
  NULL, NULL, NULL, NULL,   NULL, NULL, NULL, NULL, 
  NULL, NULL, NULL, NULL,   "&lt;"/* < */, NULL, "&gt;"/* > */
};

static const unsigned char len_table[256] = {
  1, 1, 1, 1,         1, 1, 1, 1, 
  1, 1, 1, 1,         1, 1, 1, 1, 
  1, 1, 1, 1,         1, 1, 1, 1, 
  1, 1, 1, 1,         1, 1, 1, 1, 
  
  1, 1, 6/*"*/, 1,    1, 1, 5/*&*/, 1, 
  1, 1, 1, 1,         1, 1, 1, 1, 
  1, 1, 1, 1,         1, 1, 1, 1, 
  1, 1, 1, 1,         4/*<*/, 1, 4,/*>*/ 1,
  
  1, 1, 1, 1,  1, 1, 1, 1,  1, 1, 1, 1,  1, 1, 1, 1,
  1, 1, 1, 1,  1, 1, 1, 1,  1, 1, 1, 1,  1, 1, 1, 1,
  1, 1, 1, 1,  1, 1, 1, 1,  1, 1, 1, 1,  1, 1, 1, 1,
  1, 1, 1, 1,  1, 1, 1, 1,  1, 1, 1, 1,  1, 1, 1, 1,
  
  1, 1, 1, 1,  1, 1, 1, 1,  1, 1, 1, 1,  1, 1, 1, 1,
  1, 1, 1, 1,  1, 1, 1, 1,  1, 1, 1, 1,  1, 1, 1, 1,
  1, 1, 1, 1,  1, 1, 1, 1,  1, 1, 1, 1,  1, 1, 1, 1,
  1, 1, 1, 1,  1, 1, 1, 1,  1, 1, 1, 1,  1, 1, 1, 1,

  1, 1, 1, 1,  1, 1, 1, 1,  1, 1, 1, 1,  1, 1, 1, 1,
  1, 1, 1, 1,  1, 1, 1, 1,  1, 1, 1, 1,  1, 1, 1, 1,
  1, 1, 1, 1,  1, 1, 1, 1,  1, 1, 1, 1,  1, 1, 1, 1,
  1, 1, 1, 1,  1, 1, 1, 1,  1, 1, 1, 1,  1, 1, 1, 1
};


char *smisk_xml_decode_sub(const char *src, size_t srclen, char *dst) {
  if (srclen == 0) {
    dst[0] = '\0';
    return dst;
  }
  
  while (srclen--) {
    if (*src == '&') {
      if (srclen > 3 && smisk_str5cmp(src, '&','a','m','p',';')) {
        *(dst++) = '&';
        srclen -= 4;
        src += 5;
        continue;
      }
      else if (srclen > 2 && smisk_str4cmp(src, '&','l','t',';')) {
        *(dst++) = '<';
        srclen -= 3;
        src += 4;
        continue;
      }
      else if (srclen > 2 && smisk_str4cmp(src, '&','g','t',';')) {
        *(dst++) = '>';
        srclen -= 3;
        src += 4;
        continue;
      }
      else if (srclen > 4 && smisk_str6cmp(src, '&','q','u','o','t',';')) {
        *(dst++) = '"';
        srclen -= 5;
        src += 6;
        continue;
      }
    }
    *(dst++) = *(src++);
  }
  
  return dst; /* Return address of the end of the decoded string */
}

char *smisk_xml_decode(const char *src, size_t len) {
  char *dst = (char *)malloc(len+1);
  len = smisk_xml_decode_sub(src, len, dst) - dst;
  dst[len] = '\0';
  /* if smisk_xml_decode_sub ever is able to return NULL, we should 
     modify this code to handle it */
  return dst;
}

size_t smisk_xml_encode_len(const char *s, size_t len) {
  size_t nlen = 0;
  while (len--) {
    nlen += len_table[(unsigned char)(*s++)];
  }
  return nlen;
}

char *smisk_xml_encode_sub(const char *src, size_t srclen, char *dst) {
  unsigned char len;
  char *dstp = dst;
  const char *srcp = src;
  
  while (srclen--) {
    len = len_table[(unsigned char)(*srcp)];
    if (len > 1) {
      memcpy(dstp, ent_table[(unsigned char)(*srcp)], len);
      dstp += len;
    }
    else {
      *(dstp++) = *srcp;
    }
    srcp++;
  }
  
  return dst;
}

char *smisk_xml_encode(const char *src, size_t len) {
  char *dst = NULL;
  size_t len_encoded;
  
  if (len == 0)
    return smisk_strndup(src, len);
  
  len_encoded = smisk_xml_encode_len(src, len);
  
  if (len_encoded == len)
    return smisk_strndup(src, len);
  
  dst = (char *)malloc(len_encoded+1);
  smisk_xml_encode_sub(src, len, dst);
  
  dst[len] = '\0';
  return dst;
}


PyDoc_STRVAR(smisk_xml_escape_DOC,
  "Encode reserved characters for use in XML");
PyObject *smisk_xml_escape_py(PyObject *self, PyObject *str) {
  char *orgstr, *newstr;
  Py_ssize_t orglen, len_encoded;
  PyObject *newstr_py, *unicode_str = NULL;
  
  if (!SMISK_STRING_CHECK(str)) {
    PyErr_SetString(PyExc_TypeError, "first argument must be a string");
    return NULL;
  }
  
  orglen = PyBytes_Size(str);
  
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
  
  len_encoded = smisk_xml_encode_len(orgstr, (size_t)orglen);
  
  if (len_encoded == orglen) {
    if (unicode_str) {
      Py_DECREF(str);
      str = unicode_str;
    }
    Py_INCREF(str);
    return str;
  }
  
  if ( (newstr_py = PyBytes_FromStringAndSize(NULL, len_encoded)) == NULL)
    return NULL;
  
  newstr = PyBytes_AS_STRING(newstr_py);
  
  smisk_xml_encode_sub(orgstr, (size_t)orglen, newstr);
  
  if (unicode_str) {
    Py_DECREF(str); // release utf8 intermediate copy
    str = newstr_py;
    newstr_py = PyUnicode_DecodeUTF8(newstr, len_encoded, "strict");
    Py_DECREF(str); // release intermediate newstr_py created in PyBytes_FromStringAndSize
  }
  
  return newstr_py;
}


PyDoc_STRVAR(smisk_xml_unescape_DOC,
  "Decode entities '&amp;' = '&', '&lt;' = '<', '&gt;' = '>', '&quot;' = '\"'");
PyObject *smisk_xml_unescape_py(PyObject *self, PyObject *str) {
  PyObject *dst, *unicode_str;
  char *dstp, *dstendp;
  Py_ssize_t str_len;
  
  if (PyUnicode_Check(str)) {
    unicode_str = str;
    if ( (str = PyUnicode_AsUTF8String(str)) == NULL )
      return NULL;
  }
  else if (!PyBytes_Check(str)) {
    PyErr_SetString(PyExc_TypeError, "first argument must be a str or unicode");
    return NULL;
  }
  else {
    unicode_str = NULL;
  }
  
  
  if ( (dst = PyBytes_FromStringAndSize(NULL, PyBytes_Size(str)+1)) == NULL) {
    if (unicode_str) {
      Py_DECREF(str);
    }
    return NULL;
  }
  
  str_len = PyBytes_Size(str);
  dstp = PyBytes_AS_STRING(dst);
  
  dstendp = smisk_xml_decode_sub(PyBytes_AS_STRING(str), str_len, dstp);
  
  
  if (unicode_str) {
    Py_DECREF(str); /* release temporary utf8 rep */
    PyObject *prev_dst = dst;
    dst = PyUnicode_DecodeUTF8(dstp,          /* utf-8 string */
                               dstendp - dstp /* actual length of decoded bytes */,
                               "strict"       /* strict error handling */ );
    Py_DECREF(prev_dst); /* release intermediate dst created above using PyBytes_FromStringAndSize */
  }
  else {
    /* we need to resize the str if needed */
    size_t dst_len = dstendp - dstp;
    if ( (dst_len < str_len) && (_PyBytes_Resize(&dst, dst_len) == -1) ) {
      return NULL;
    }
  }
  
  
  return dst;
}

/* -------------------------------------------------------------------------- */

#pragma mark -
#pragma mark Type construction

static PyMethodDef methods[] = {
  {"escape",   (PyCFunction)smisk_xml_escape_py,   METH_O, smisk_xml_escape_DOC},
  {"unescape", (PyCFunction)smisk_xml_unescape_py, METH_O, smisk_xml_unescape_DOC},
  {NULL, NULL, 0, NULL}
};

PyObject *smisk_xml_register (PyObject *parent) {
  log_trace("ENTER");
  
  if ((smisk_xml = Py_InitModule("smisk.core.xml", methods)) == NULL) {
    log_error("Py_InitModule(\"smisk.core.xml\", methods) failed");
    return NULL;
  }
  
  PyModule_AddStringConstant(smisk_xml, "__doc__", "XML functions");
  
  if (PyModule_AddObject(parent, "xml", smisk_xml) != 0) {
    log_error("PyModule_AddObject(parent, \"xml\", smisk_xml) != 0");
    Py_DECREF(smisk_xml);
    return NULL;
  }
  
  return smisk_xml;
}

