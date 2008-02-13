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
#include "cstr.h"
#include <string.h>
#include <stdlib.h>

/*
typedef struct {
	char* ptr;
  size_t growsize;
	size_t size;
	size_t length;
} cstr;
*/

int cstr_init (cstr_t *s, size_t capacity, unsigned int growsize) {
  if(growsize == 0) {
    growsize = capacity;
  }
  s->ptr = (char *)malloc(sizeof(char)*(capacity+1));
  if(s->ptr != NULL) {
    s->ptr[0] = 0;
  }
  s->growsize = growsize;
  s->size = capacity;
  s->length = 0;
  return (s->ptr == NULL);
}

void cstr_free(cstr_t *s) {
  if(s->ptr) {
    free(s->ptr);
  }
}

void cstr_reset(cstr_t *s) {
  s->length = 0;
  s->ptr[0] = 0;
}

int cstr_resize(cstr_t *s, const size_t increment) {
  size_t new_size;
  if(increment < s->growsize) {
		new_size = s->size + s->growsize + 1;
	} else {
	  new_size = s->size + increment + 1;
	}
  char *new = (char *)realloc(s->ptr, sizeof(char)*new_size);
  if(new != NULL) {
    s->ptr = new;
    s->size = new_size;
  } else {
    return 1;
  }
  return 0;
}

int cstr_ensure_freespace(cstr_t *s, const size_t space) {
  if(s->size - s->length < space) {
    return cstr_resize(s, space - (s->size - s->length));
  }
  return 0;
}

int cstr_append(cstr_t *s, const char *src, const size_t srclen) {
  if(s->size - s->length <= srclen) {
    if(!cstr_resize(s, srclen)) {
      return 1;
    }
  }
  memcpy(s->ptr + s->length, src, srclen);
  s->length += srclen;
  s->ptr[s->length] = 0;
  return 0;
}

int cstr_appendc(cstr_t *s, const char ch) {
  if(s->length >= s->size) {
    if(cstr_resize(s, (size_t)1)) {
      return 1;
    }
  }
  s->ptr[s->length++] = ch;
  s->ptr[s->length] = 0;
  return 0;
}

char cstr_popc(cstr_t *s) {
  if(s->length) {
    char ch = s->ptr[s->length--];
    s->ptr[s->length] = 0;
    return ch;
  }
  return (char)0;
}
