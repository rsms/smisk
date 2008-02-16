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
#ifndef SMISK_UTILS_H
#define SMISK_UTILS_H
#include <fcgiapp.h>

// Returns PyStringObject (borrowed reference)
PyObject* format_exc (void);

// Return ISO timestamp YYYY-MM-DD HH:MM:SS
// @return newly allocated string. You must free the resulting string yourself.
char *timestr (struct tm *time_or_null);

// Associate value with key - if the key exists, the keys value is a list of values.
int PyDict_assoc_val_with_key (PyObject *dict, PyObject *val, PyObject *key);

// Parse input data (query string, post url-encoded, cookie, etc). Returns 0 on success.
int parse_input_data (char *s, const char *separator, int is_cookie_data, PyObject *dict);

// Read a line from a FCGI stream
size_t smisk_stream_readline (char *str, int n, FCGX_Stream *stream);

// Print bytes - unsafe or outside ASCII characters are printed as \xXX
// Will print something like: bytes(4) 'm\x0dos'
void frepr_bytes (FILE *f, const char *s, size_t len);

// Quick way to find out if a file exists. May not be bullet proof, for when
// example a file exists, but is not accessible.
int file_exist (const char *fn);

// Current time in microseconds
double microtime (void);

// KB, GB, etc
char nearest_size_unit (double *bytes);

#endif
