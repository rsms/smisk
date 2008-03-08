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
#include <stdio.h>
#include <unistd.h>
#include <signal.h>
#include <ctype.h>
#include "__init__.h"
#include "utils.h"
#include "multipart.h"
#include "cstr.h"

#define print(fmt, ...) fprintf(stderr, "Multipart: %s:%d: " fmt "\n", __FILE__, __LINE__, ##__VA_ARGS__)

#define BOUNDARY_HIT_TEST(_s_) \
 ((_s_[0] == '-') && (_s_[1] == '-') && (strncmp(_s_, ctx->boundary, ctx->boundary_len) == 0))

typedef struct {
  char *lbuf2; // used for file reading as line tail
  long content_length;
  int error;
  cstr_t buf;
  char *boundary;
  size_t boundary_len;
  char *filename;
  char *content_type;
  char *part_name;
  FCGX_Stream *stream;
  PyObject *post;
  PyObject *files;
  int eof;
} multipart_ctx_t;


void smisk_multipart_ctx_reset(multipart_ctx_t *ctx) {
  ctx->stream = NULL;
  ctx->content_length = 0;
  ctx->error = 0;
  ctx->eof = 0;
  ctx->boundary_len = 0;
  cstr_reset(&ctx->buf);
  ctx->boundary[0] = 0;
  ctx->filename[0] = 0;
  ctx->content_type[0] = 0;
  ctx->part_name[0] = 0;
}


// return 0 on success, !0 on malloc() failure
int smisk_multipart_ctx_init(multipart_ctx_t *ctx) {
  if(cstr_init(&ctx->buf, SMISK_STREAM_READLINE_LENGTH+1, 0) != 0) return -1;
  if((ctx->lbuf2 = (char *)malloc(SMISK_STREAM_READLINE_LENGTH+1)) == NULL) return -1;
  if((ctx->boundary = (char *)malloc(SMISK_STREAM_READLINE_LENGTH+1)) == NULL) return -1;
  if((ctx->filename = (char *)malloc(FILENAME_MAX+1)) == NULL) return -1;
  if((ctx->content_type = (char *)malloc(FILENAME_MAX+1)) == NULL) return -1;
  if((ctx->part_name = (char *)malloc(FILENAME_MAX+1)) == NULL) return -1;
  smisk_multipart_ctx_reset(ctx);
  return 0;
}


void smisk_multipart_ctx_free(multipart_ctx_t *ctx) {
  cstr_free(&ctx->buf);
  if(ctx->boundary) free(ctx->boundary);
  if(ctx->content_type) free(ctx->content_type);
  if(ctx->part_name) free(ctx->part_name);
  if(ctx->lbuf2) free(ctx->lbuf2);
}


char *smisk_multipart_mktmpfile(multipart_ctx_t *ctx) {
  char *fn = tempnam(SMISK_FILE_UPLOAD_DIR, SMISK_FILE_UPLOAD_PREFIX);
  log_debug("Creating temporary file '%s'", fn);
  if(fn == NULL) {
    PyErr_Format(smisk_IOError, "Failed to create temporary file at dir '%s' with prefix '%s'",
      SMISK_FILE_UPLOAD_DIR, SMISK_FILE_UPLOAD_PREFIX);
    return NULL;
  }
  return fn;
}


// return 0 on success, !0 on error
int smisk_multipart_parse_file(multipart_ctx_t *ctx) {
  char *fn = NULL, *e;
  FILE *f = NULL;
  ssize_t bw;
  size_t bytes = 0;
  IFDEBUG(double timer = microtime());
  
  // Read line and write line
  char *lbuf1, *lbuf2, *p;
  size_t lbuf1_len, lbuf2_len;
  int boundary_hit;
  
  lbuf1 = ctx->buf.ptr;
  lbuf2 = ctx->lbuf2;
  *lbuf1 = 0;
  *lbuf2 = 0;
  lbuf1_len = 0;
  lbuf2_len = 0;
  boundary_hit = 0;
  
  while( (!boundary_hit) && 
         (lbuf1_len = smisk_stream_readline(lbuf1, SMISK_STREAM_READLINE_LENGTH, ctx->stream)) )
  {
    if(BOUNDARY_HIT_TEST(lbuf1)) {
      e = ctx->buf.ptr; for(;( (*e != '\r') && (*e != '\0') ); e++); // find end
      if( (e > ctx->buf.ptr+2) && (*(e-1) == '-') && (*(e-2) == '-') ) {
        //print("  > hit end boundary - end of message");
        ctx->eof = 1;
      }
      /*else {
        print("  > hit boundary - end of part");
      }*/
      boundary_hit = 1;
    }
    
    // write prev line
    if(lbuf2_len > 1) {
      if(boundary_hit) {
        // last line includes \r\n which is not part of the file
        lbuf2_len -= 2;
      }
      if(lbuf2_len) {
        if(f == NULL) {
          // Lazy tempfile creation
          if( (fn = smisk_multipart_mktmpfile(ctx)) == NULL ) {
            // PyErr has been set by smisk_multipart_mktmpfile
            return 1;
          }
          if((f = fopen(fn, "w")) == NULL) {
            PyErr_SetFromErrnoWithFilename(PyExc_IOError, __FILE__);
            return 1;
          }
        }
        bw = fwrite((const void *)lbuf2, 1, lbuf2_len, f);
        if(bw == -1) {
          fclose(f);
          PyErr_SetFromErrnoWithFilename(PyExc_IOError, __FILE__);
          return 1;
        }
        bytes += bw;
      }
    }
    
    // switch line buffers
    p = lbuf1;
    lbuf1 = lbuf2;
    lbuf2 = p;
    lbuf2_len = lbuf1_len;
  }
  
  IFDEBUG(if(bytes) {
    timer = microtime()-timer;
    double adjusted_size = (double)bytes;
    char size_unit = nearest_size_unit(&adjusted_size);
    log_debug("Stats for part '%s': %.2f %c/sec (Parse time: %.3f sec, Size: %.1f %c)",
      ctx->part_name,
      adjusted_size/timer, size_unit,
      timer,
      adjusted_size, size_unit
      );
  });
  
  // Close file
  fclose(f);
  
  // Create file record
  PyObject *py_key = PyString_FromString(ctx->part_name);
  
  if(bytes) {
    // XXX Until further fix, we create a dict with the information
    PyObject *m = PyDict_New();
    PyDict_SetItemString(m, "filename",     PyString_FromString(ctx->filename));
    PyDict_SetItemString(m, "content_type", PyString_FromString(ctx->content_type));
    PyDict_SetItemString(m, "path",         PyString_FromString(fn));
    PyDict_SetItemString(m, "size",         PyLong_FromUnsignedLong(bytes));
    
    if(PyDict_assoc_val_with_key(ctx->files, m, py_key) != 0) {
      return -1;
    }
  }
  else {
    // no value, only key
    if(PyDict_assoc_val_with_key(ctx->files, Py_None, py_key) != 0) {
      return -1;
    }
  }
  
  return 0;
}



int smisk_multipart_parse_form_data(multipart_ctx_t *ctx) {
  size_t bytes_read, len;
  char *p, *e;
  
  // Read line and write line
  p = ctx->buf.ptr;
  while((bytes_read = smisk_stream_readline(p, SMISK_STREAM_READLINE_LENGTH, ctx->stream))) {
    if(BOUNDARY_HIT_TEST(p)) {
      e = p; for(;( (*e != '\r') && (*e != '\0') ); e++); // find end
      if( (e > p+2) && (*(e-1) == '-') && (*(e-2) == '-') ) {
        //print("  > hit end boundary - end of message");
        ctx->eof = 1;
      }
      else {
        //print("  > hit boundary - end of part ('%s')", p);
      }
      *p = 0; // terminate before boundary start
      break;
    }
    p += bytes_read;
    if(cstr_ensure_freespace(&ctx->buf, SMISK_STREAM_READLINE_LENGTH) != 0) {
      log_error("malloc() failed!");
      return 1;
    }
  }
  
  PyObject *py_key = PyString_FromString(ctx->part_name);
  if( (len = (p - ctx->buf.ptr)) > 2 ) {
    *(p-2) = '\0'; // \r\n -> \0\n
    len -= 2; // because above line
    if(PyDict_assoc_val_with_key(ctx->post, PyString_FromString(ctx->buf.ptr), py_key) != 0) {
      return -1;
    }
  }
  else {
    // no value, only key
    if(PyDict_assoc_val_with_key(ctx->post, Py_None, py_key) != 0) {
      return -1;
    }
  }
  
  return 0;
}


// return 0 on success, !0 on error
int smisk_multipart_parse_part(multipart_ctx_t *ctx) {
  char *p, *buf, is_file = 0;
  
  buf = ctx->buf.ptr;
  
  ctx->filename[0] = 0;
  ctx->content_type[0] = 0;
  
  // Parse headers
  while( FCGX_GetLine(buf, SMISK_STREAM_READLINE_LENGTH, ctx->stream) ) {
    if((buf[0] == '\r') && (buf[1] == '\n') && (buf[2] == '\0')) {
      // end of headers
      break;
    }
    if(strncasecmp(buf, "Content-Disposition:", 20) == 0) {
      char *ssp = buf+20;
      char *key, *val, *p;
      int keylen;
      while( (val = strsep(&ssp, ";")) ) {
        STR_LTRIM_S(val);
        if((p = strchr(val, '='))) { // key=value
          *p = 0; // terminate part where val begin
          keylen = p-val;
          key = val;
          val = p;
          val++;
          if(*val == '"') { // value is quoted
            val++;
            p = val; for(;(*p != '"') && (*p != '\r'); p++); *p = 0; // rterm
          }
          // tests
          if(STR_EQUALS_4(key, "name")) {
            strncpy(ctx->part_name, val, FILENAME_MAX);
          }
          else if(STR_EQUALS_8(key, "filename")) {
            strncpy(ctx->filename, val, FILENAME_MAX);
            is_file = 1;
          }
          /*else {
            print("unused key-value: '%s'='%s'", key, val);
          }*/
        }
        /*else { // not key=value
          print("unused value: '%s'", val);
        }*/
      }
    }
    else if(strncasecmp(buf, "Content-Type:", 13) == 0) {
      buf += 13;
      STR_LTRIM_S(buf);
      if( (p = strchr(buf, '\r')) ) {
        *p = 0;
        strncpy(ctx->content_type, buf, FILENAME_MAX);
      }
    }
  }
  
  if((ctx->part_name) && (*ctx->part_name)) {
    // Parse body
    if(is_file) {
      // file
      if(smisk_multipart_parse_file(ctx) != 0) return 1;
    }
    else {
      // form data
      if(smisk_multipart_parse_form_data(ctx) != 0) return 1;
    }
  }
  else {
    log_error("One or several parts in multipart post data missing name-attribute. Skipping input body parsing.");
    ctx->eof = 1;
  }
  
  return 0;
}

// For now, we keep one instance in shared memory for use by the whole process.
// This can be easily changed in the future, as itäs only referenced to by
// smisk_multipart_parse_stream(), thus adding a context attribute and removing
// will be all that takes.
static multipart_ctx_t __ctx = {NULL};


int smisk_multipart_parse_stream (FCGX_Stream *stream, long content_length, PyObject *post, PyObject *files) {
  //multipart_ctx_t ctx;
  int status = 0;
  size_t bytes_read;
  
  if(content_length <= 0) {
    return 0;
  }
  
  // init context
  if(__ctx.lbuf2 == NULL) {
    if(smisk_multipart_ctx_init(&__ctx)) {
      log_error("malloc() failed!");
      raise(9);
    }
  }
  else {
    smisk_multipart_ctx_reset(&__ctx);
  }
  
  // Attach context info
  __ctx.stream = stream;
  __ctx.content_length = content_length;
  __ctx.post = post;
  __ctx.files = files;
  
  // find boundary
  if((bytes_read = smisk_stream_readline(__ctx.boundary, SMISK_STREAM_READLINE_LENGTH, __ctx.stream))) {
    __ctx.boundary_len = bytes_read-2; // -2 = -\r\n
    __ctx.boundary[__ctx.boundary_len] = 0;
  
    // We got our first part, so let's get going
    int limit=9;
    while((!__ctx.eof) && limit--) {
      if((status = smisk_multipart_parse_part(&__ctx)) != 0) {
        break;
      }
    }
  }
  
  //smisk_multipart_ctx_free(&__ctx);
  return status;
}

