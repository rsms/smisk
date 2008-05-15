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
#ifndef SMISK_UTILS_H
#define SMISK_UTILS_H

#include <fcgiapp.h>


/** @return PyStringObject (borrowed reference). Does NOT clear exception. */
PyObject *smisk_format_exc (PyObject *type, PyObject *value, PyObject *tb);

/**
 * Associate value with key - if the key exists, the keys value is a list of
 * values.
 */
int PyDict_assoc_val_with_key (PyObject *dict, PyObject *val, PyObject *key);

/**
 * Parse input data (query string, post url-encoded, cookie, etc).
 * @return 0 on success.
 */
int smisk_parse_input_data (char *s, const char *separator, int is_cookie_data, PyObject *dict);

/** Read a line from a FCGI stream */
size_t smisk_stream_readline (char *str, int n, FCGX_Stream *stream);

/**
 * Print bytes - unsafe or outside ASCII characters are printed as \xXX
 * Will print something like: bytes(4) 'm\x0dos'
 */
void smisk_frepr_bytes (FILE *f, const char *s, size_t len);

/** @return Current time in microseconds */
double smisk_microtime (void);

/** KB, GB, etc */
char smisk_size_unit (double *bytes);

/**
 * Encode bytes into printable ASCII characters.
 * Returns a pointer to the byte after the last valid character in out.
 * 
 * nbits=4: out need to fit 40+1 bytes (base 16) (0-9, a-f)
 * nbits=5: out need to fit 32+1 bytes (base 32) (0-9, a-v)
 * nbits=6: out need to fit 27+1 bytes (base 64) (0-9, a-z, A-Z, "-", ",")
 */
char *smisk_encode_bin (char *in, size_t inlen, char *out, char bits_per_byte);

/**
 * @param  list    list
 * @param  prefix  string
 * @return int
 */
PyObject *smisk_find_string_by_prefix_in_dict(PyObject *list, PyObject *prefix);

#endif
