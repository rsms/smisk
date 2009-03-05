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
#ifndef SMISK_XML_H
#define SMISK_XML_H

// C API
size_t smisk_xml_encode_len(const char *s, size_t len);
char *smisk_xml_encode_sub(const char *src, size_t srclen, char *dst);
char *smisk_xml_encode(const char *s, size_t len);
char *smisk_xml_decode_sub(const char *src, size_t srclen, char *dst);
char *smisk_xml_decode(const char *src, size_t len);

// module smisk.xml (the smisk.xml module object)
extern PyObject *smisk_xml;

// Type setup
PyObject *smisk_xml_register(PyObject *parent);


#endif
