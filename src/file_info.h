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
#ifndef SMISK_FILE_INFO_H
#define SMISK_FILE_INFO_H

#include <stdio.h>
#if HAVE_SYS_TIME_H
  #include <sys/time.h>
#endif

// XXX set these at configure-time
#define HAVE_UTIMES 1
#define HAVE_UTIME 1

/**
 * Quick way to find out if a file exists. May not be bullet proof, for when
 * example a file exists, but is not accessible.
 */
int smisk_file_exist (const char *fn);

/**
 * Get modified time for file pointed to by either descriptor fd or name fn.
 *
 * @param fn  if not used, set to NULL
 * @param fd  if not used, set to -1
 * @return  Returns 0 on error. (You can check errno for errors)
 */
time_t smisk_file_mtime (const char *fn, int fd);

/** @return 0 on success */
int smisk_file_mtime_set (const char *fn, int fd, struct timeval mtime);

/** @return 0 on success */
int smisk_file_mtime_set_now (const char *fn, int fd);

#endif
