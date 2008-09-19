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
#include <arpa/inet.h>
#include "__init__.h"
#include "uid.h"
#include "utils.h"
#include "sha1.h"


int smisk_uid_create(smisk_uid_t *uid, const char *node, size_t node_length) {
  struct timeval tv;
  sha1_ctx_t sha1_ctx;
  
  struct data {
    time_t      tv_sec;
    suseconds_t tv_usec;
    pid_t       pid;
    long        salt;
  };
  
  gettimeofday(&tv, NULL);
  srandom(tv.tv_usec);
  
  struct data d;
  d.tv_sec = htonl(tv.tv_sec);
  d.tv_usec = htonl(tv.tv_usec);
  d.pid = htonl(getpid());
  d.salt = random();
  
  sha1_init(&sha1_ctx);
  sha1_update(&sha1_ctx, (byte *)&d, sizeof(d));
  
  if ((node != NULL) && node_length)
    sha1_update(&sha1_ctx, (byte *)node, node_length);
  
  sha1_final(&sha1_ctx, uid->digest);
  
  return 0;
}


PyObject *smisk_uid_format(smisk_uid_t *uid, int nbits) {
  PyObject *s;
  switch(nbits) {
    case 6:
      s = PyString_FromStringAndSize(NULL, 27);
      break;
    case 5:
      s = PyString_FromStringAndSize(NULL, 32);
      break;
    case 4:
      s = PyString_FromStringAndSize(NULL, 40);
      break;
    default:
      return PyErr_Format(PyExc_ValueError, "Invalid number of bits: %d", nbits);
  }
  char *digest_buf = PyString_AS_STRING(s);
  smisk_encode_bin(uid->digest, 20, digest_buf, nbits);
  return s;
}