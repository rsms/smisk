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
#ifndef SMISK_UTILS_H
#define SMISK_UTILS_H

#include <fcgiapp.h>

/** Like PyBytes_FromStringAndSize but filters src through lower() */
PyObject *smisk_PyBytes_FromStringAndSize_lower (const char *src, Py_ssize_t length);

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
int smisk_parse_input_data (char *s, const char *separator, int is_cookie_data, 
                            PyObject *dict, const char *charset);

/** Read a line from a FCGI stream */
int smisk_stream_readline (char *str, int n, FCGX_Stream *stream);

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
char *smisk_encode_bin (const byte *in, size_t inlen, char *out, char bits_per_byte);

/**
 * Pack bytes into printable ASCII characters.
 * Returns a PyString.
 * See smisk_encode_bin for more information.
 */
PyObject *smisk_util_pack (const byte *data, size_t size, int nbits);

/**
 * @param  list    list
 * @param  prefix  string
 */
PyObject *smisk_find_string_by_prefix_in_dict (PyObject *list, PyObject *prefix);

/**
 * Callback signature for probably_call()
 */
typedef int probably_call_cb(void *arg1);

/**
 * Calls cb depending on probability.
 *
 * @param probability float Likeliness of cb being called. A value between 0 and 1.
 * @param cb                Function to call.
 * @param cb_arg            Arbirtrary argument to be passed on to cb when called.
 * @returns int             -1 on error (if so, a Python Error have been set) or 0 on
 *                          success.
 */
int probably_call (float probability, probably_call_cb *cb, void *cb_arg);

/**
 * Calculate a hash from any python object.
 *
 * If obj support hash out-of-the-box, the equivalent of hash(obj) will be
 * used. Otherwise obj will be marshalled and the resulting bytes are used for
 * calculating the hash.
 */
long smisk_object_hash (PyObject *obj);


/**
 * Re-encode str if needed.
 * Returns -1 on failure and 0 on success.
 * On error, exception is set, -1 returned and str is NOT touched.
 */
int smisk_str_recode( PyObject **str, const char *src_charset, const char *dst_charset,
  const char *errors );

/**
 * Decode str into unicode.
 * Returns -1 on failure and 0 on success.
 * On error, exception is set, -1 returned and str is NOT touched.
 * Decrements str and returns new reference to new unicode object.
 */
int smisk_str_to_unicode( PyObject **str, const char *charset, const char *errors );

#endif
