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
#ifndef CSTR_H
#define CSTR_H

#define CSTR_VERSION "$Id: cstr.h 7 2007-10-18 04:08:08Z rasmus $"

#include <stddef.h>

typedef struct {
	char* ptr;
  unsigned int growsize;
	size_t size;
	size_t length;
} cstr_t;

int cstr_init (cstr_t *s, size_t capacity, unsigned int growsize); // return 0 on success, 1 on malloc failure
void cstr_free (cstr_t *s);
void cstr_reset (cstr_t *s);
int cstr_resize (cstr_t *s, const size_t increment);
int cstr_ensure_freespace (cstr_t *s, const size_t space);
int cstr_append (cstr_t *s, const char *src, const size_t srclen);
int cstr_appendc (cstr_t *s, const char ch);
char cstr_popc (cstr_t *s);

#endif
