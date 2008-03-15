/* Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/*
 * This code has been modified for the Smisk project by Rasmus Andersson.
 */
#include <stdio.h>
#include <errno.h>
#if HAVE_FCNTL_H
#include <fcntl.h>
#endif
#ifdef HAVE_SYS_FILE_H
#include <sys/file.h>
#endif

#include "file_lock.h"

int smisk_file_lock(FILE *fh, int type) {
  int rc, fd = fileno(fh); /* fileno should not fail and do not set the 
                                     external variable errno. */
  
#if defined(HAVE_FCNTL_H)
  {
    struct flock l = { 0 };
    int fc;

    l.l_whence = SEEK_SET;  /* lock from current point */
    l.l_start = 0;      /* begin lock at this offset */
    l.l_len = 0;      /* lock to end of file */
    if (type & SMISK_FILE_LOCK_SHARED)
      l.l_type = F_RDLCK;
    else
      l.l_type = F_WRLCK;
    
    fc = (type & SMISK_FILE_LOCK_NONBLOCK) ? F_SETLK : F_SETLKW;

    /* keep trying if fcntl() gets interrupted (by a signal) */
    while ((rc = fcntl(fd, fc, &l)) < 0 && errno == EINTR)
      continue;

    if (rc == -1) {
      /* on some Unix boxes (e.g., Tru64), we get EACCES instead
       * of EAGAIN; we don't want APR_STATUS_IS_EAGAIN() matching EACCES
       * since that breaks other things, so fix up the retcode here
       */
      if (errno == EACCES) {
        return EAGAIN;
      }
      return errno;
    }
  }
#elif defined(HAVE_SYS_FILE_H)
  {
    int ltype;

    if ((type & SMISK_FILE_LOCK_SHARED) != 0)
      ltype = LOCK_SH;
    else
      ltype = LOCK_EX;
    if ((type & SMISK_FILE_LOCK_NONBLOCK) != 0)
      ltype |= LOCK_NB;

    /* keep trying if flock() gets interrupted (by a signal) */
    while ((rc = flock(fd, ltype)) < 0 && errno == EINTR)
      continue;

    if (rc == -1)
      return errno;
  }
#else
#error No file locking mechanism is available.
#endif

  return 0;
}


int smisk_file_unlock(FILE *fh) {
  int rc, fd = fileno(fh);
  
#if defined(HAVE_FCNTL_H)
  {
    struct flock l = { 0 };

    l.l_whence = SEEK_SET;  /* lock from current point */
    l.l_start = 0;      /* begin lock at this offset */
    l.l_len = 0;      /* lock to end of file */
    l.l_type = F_UNLCK;

    /* keep trying if fcntl() gets interrupted (by a signal) */
    while ((rc = fcntl(fd, F_SETLKW, &l)) < 0
         && errno == EINTR)
      continue;

    if (rc == -1)
      return errno;
  }
#elif defined(HAVE_SYS_FILE_H)
  {
    /* keep trying if flock() gets interrupted (by a signal) */
    while ((rc = flock(fd, LOCK_UN)) < 0 && errno == EINTR)
      continue;

    if (rc == -1)
      return errno;
  }
#else
#error No file locking mechanism is available.
#endif

  return 0;
}
