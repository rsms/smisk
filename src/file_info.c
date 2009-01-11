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
#include <errno.h>
#include <unistd.h>
#if HAVE_SYS_STAT_H
#include <sys/stat.h>
#endif

#include "time.h"
#include "file_info.h"


int smisk_file_exist(const char *fn) {
  return ((access(fn, R_OK) == 0) ? 1 : 0);
}


time_t smisk_file_mtime (const char *fn, int fd) {
  struct stat st;
  int r = -1;
  
  if (fd != -1)
    r = fstat(fd, &st);
  else
    r = stat(fn, &st);
  
  return (r != 0) ? 0 : st.st_mtime;
}


int smisk_file_mtime_set (const char *fn, int fd, struct timeval mtime) {
  int status;
  struct stat finfo;
  
  if (fd != -1)
    status = fstat(fd, &finfo);
  else
    status = stat(fn, &finfo);
  
  if (status != 0)
    return status;

#ifdef HAVE_UTIMES
  {
    struct timeval tvp[2];
    
    tvp[0].tv_sec = finfo.st_mtime;
    tvp[0].tv_usec = 0;
    tvp[1] = mtime;
    
    if (fd != -1)
      status = futimes(fd, tvp);
    else
      status = utimes(fn, tvp);
  }
#elif defined(HAVE_UTIME)
  {
    if (fn == NULL) {
      log_error("fn must be set (this system does not have utimes)");
      return -1;
    }
    
    struct utimbuf buf;
    
    buf.actime = finfo.st_atime;
    buf.modtime = mtime.tv_sec;
    
    if (utime(fn, &buf) == -1) {
      return errno;
    }
  }
#else
  #warning smisk_file_mtime_set disabled as neither utimes not utime is available
  return -1;
#endif
  if (status == -1)
    return errno;
  
  return 0;
}


int smisk_file_mtime_set_now (const char *fn, int fd) {
#ifdef HAVE_UTIMES
  {
    if (fd != -1)
      return futimes(fd, NULL);
    else
      return utimes(fn, NULL);
  }
#elif defined(HAVE_UTIME)
  {
    if (fn == NULL) {
      log_error("fn must be set (this system does not have utimes)");
      return -1;
    }
    return utime(fn, NULL);
  }
#else
  #warning smisk_file_mtime_set_now disabled as neither utimes not utime is available
  return -1;
#endif
  
  return 0;
}

