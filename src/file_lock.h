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
#ifndef SMISK_FILE_LOCK_H
#define SMISK_FILE_LOCK_H

#define SMISK_FILE_LOCK_SHARED 1
#define SMISK_FILE_LOCK_NONBLOCK 2


/**
 * Aquire a file lock, similar to libc flock().
 * 
 * @param type  Bitmask constructed by and of SMISK_FLOCK_*.
 *              If SMISK_FLOCK_SHARED is not included, an exclusive lock
 *              is aquired.
 * @return 0 on success, otherwise -1 or errno.
 */
int smisk_file_lock (FILE *fh, int type);


/**
 * Release a file lock previously aquired using smisk_file_lock.
 *
 * @return 0 on success, otherwise -1 or errno.
 */
int smisk_file_unlock (FILE *fh);

#endif