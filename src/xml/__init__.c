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
#include "../__init__.h"
#include "__init__.h"
#include <structmember.h>

#define IS_RESERVED(c) (chr_table[(unsigned char)(c)])

PyObject *smisk_xml = NULL; // the module

#pragma mark C API only

static const unsigned char chr_table[256] =
{
  1,  1,  1,  1,   1,  1,  1,  1,   /* NUL SOH STX ETX  EOT ENQ ACK BEL */
  1,  0,  0,  1,   1,  0,  1,  1,   /* BS  HT  LF  VT   FF  CR  SO  SI  */
  1,  1,  1,  1,   1,  1,  1,  1,   /* DLE DC1 DC2 DC3  DC4 NAK SYN ETB */
  1,  1,  1,  1,   1,  1,  1,  1,   /* CAN EM  SUB ESC  FS  GS  RS  US  */
  0,  0,  1,  0,   0,  0,  1,  0,   /* SP  !   "   #    $   %   &   '   */
  0,  0,  0,  0,   0,  0,  0,  0,   /* (   )   *   +    ,   -   .   /   */
  0,  0,  0,  0,   0,  0,  0,  0,   /* 0   1   2   3    4   5   6   7   */
  0,  0,  0,  0,   1,  0,  1,  0,   /* 8   9   :   ;    <   =   >   ?   */
  0,  0,  0,  0,   0,  0,  0,  0,   /* @   A   B   C    D   E   F   G   */
  0,  0,  0,  0,   0,  0,  0,  0,   /* H   I   J   K    L   M   N   O   */
  0,  0,  0,  0,   0,  0,  0,  0,   /* P   Q   R   S    T   U   V   W   */
  0,  0,  0,  0,   0,  0,  0,  0,   /* X   Y   Z   [    \   ]   ^   _   */
  0,  0,  0,  0,   0,  0,  0,  0,   /* `   a   b   c    d   e   f   g   */
  0,  0,  0,  0,   0,  0,  0,  0,   /* h   i   j   k    l   m   n   o   */
  0,  0,  0,  0,   0,  0,  0,  0,   /* p   q   r   s    t   u   v   w   */
  0,  0,  0,  0,   0,  0,  0,  0,   /* x   y   z   {    |   }   ~   DEL */

  0, 0, 0, 0,  0, 0, 0, 0,  0, 0, 0, 0,  0, 0, 0, 0,
  0, 0, 0, 0,  0, 0, 0, 0,  0, 0, 0, 0,  0, 0, 0, 0,
  0, 0, 0, 0,  0, 0, 0, 0,  0, 0, 0, 0,  0, 0, 0, 0,
  0, 0, 0, 0,  0, 0, 0, 0,  0, 0, 0, 0,  0, 0, 0, 0,

  0, 0, 0, 0,  0, 0, 0, 0,  0, 0, 0, 0,  0, 0, 0, 0,
  0, 0, 0, 0,  0, 0, 0, 0,  0, 0, 0, 0,  0, 0, 0, 0,
  0, 0, 0, 0,  0, 0, 0, 0,  0, 0, 0, 0,  0, 0, 0, 0,
  0, 0, 0, 0,  0, 0, 0, 0,  0, 0, 0, 0,  0, 0, 0, 0,
};


/* The core of url_escape_* functions.  Escapes the characters that
   match the provided mask in urlchr_table.*/

void smisk_xml_encode_p (const char *s, size_t len, char *dest) {
  const char *p1;
  char *p2;
  
  p1 = s;
  p2 = dest;
  
  while (len--) {
    // Quote the characters that match the test mask.
    if (IS_RESERVED(*p1)) {
      unsigned char c = *p1++;
      *p2++ = '&'; *p2++ = '#'; *p2++ = 'x';
      *p2++ = XNUM_TO_DIGIT (c >> 4);
      *p2++ = XNUM_TO_DIGIT (c & 0xf);
      *p2++ = ';';
    }
    else {
      *p2++ = *p1++;
    }
  }
  
  *p2 = '\0';
}

size_t smisk_xml_encode_newlen(const char *s, size_t len) {
  size_t nlen = len;
  while (len--) {
    if ( IS_RESERVED(*s++) ) {
      nlen += 5;
    }
  }
  return nlen;
}

char *smisk_xml_encode (const char *s, size_t len) {
  char *dest;
  size_t nlen;
  
  nlen = smisk_xml_encode_newlen(s, len);
  
  if (nlen == len)
    return strdup(s);
  else
    dest = (char *)malloc(nlen+1);
  
  smisk_xml_encode_p(s, len, dest);
  
  return dest;
}


PyDoc_STRVAR(smisk_xml_encode_DOC,
  "Encode reserved and unsafe characters for use in XML or HTML context.\n"
  "\n"
  "Example:\n"
  "\n"
  ">>> from smisk.core.xml import encode\n"
  ">>> s = \"Your's & not mine <says> \\\"you\\\"\"\n"
  ">>> encode(s)\n"
  "\"Your's &#x26; not mine &#x3C;says&#x3E; &#x22;you&#x22;\"\n"
  ">>> \n"
  "\n"
  ":param s: Raw string to be encoded"
  ":type  s: string\n"
  ":rtype: string");
PyObject *smisk_xml_encode_py(PyObject *self, PyObject *pys) {
  size_t len, nlen;
  PyObject *npys;
  char *s, *dest;
  int should_decref_pys = 0;
  
  if (!PyString_CheckExact(pys)) {
    if (PyUnicode_Check(pys)) {
      // Unicode (UTF-16?) to UTF-8
      if ( (pys = PyUnicode_AsUTF8String(pys)) == NULL)
        return NULL;
      
      should_decref_pys = 1;
    }
    else {
      PyErr_SetString(PyExc_TypeError, "first argument must be a string");
      return NULL;
    }
  }
  
  len = (size_t)PyString_GET_SIZE(pys);
  s = PyString_AS_STRING(pys);
  nlen = smisk_xml_encode_newlen(s, len);
  
  if (nlen == len) {
    Py_INCREF(pys);
    return pys;
  }
  
  npys = PyString_FromStringAndSize(NULL,(Py_ssize_t)nlen);
  if (npys == NULL) {
    if (should_decref_pys) {
      Py_DECREF(pys);
    }
    return NULL;
  }
  dest = PyString_AS_STRING(npys);
  
  smisk_xml_encode_p(s, len, dest);
  
  if (should_decref_pys) {
    Py_DECREF(pys);
  }
  
  return npys;
}



#pragma mark -
#pragma mark Type construction

static PyMethodDef methods[] = {
  {"encode", (PyCFunction)smisk_xml_encode_py, METH_O, smisk_xml_encode_DOC},
  {NULL, NULL, 0, NULL}
};

PyDoc_STRVAR(smisk_xml_DOC,
  "XML-related utilities");

PyObject *smisk_xml_register (PyObject *parent) {
  log_debug("ENTER smisk_xml_register");
  smisk_xml = Py_InitModule("smisk.core.xml", methods);
  PyModule_AddStringConstant(smisk_xml, "__doc__", smisk_xml_DOC);
  if (PyModule_AddObject(parent, "xml", smisk_xml) != 0) {
    Py_DECREF(smisk_xml);
    return NULL;
  }
  return smisk_xml;
}

