/*
Copyright (c) 2007-2008 Rasmus Andersson

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
#ifndef SMISK_CONFIG_H
#define SMISK_CONFIG_H

#include "system_config.h"

// If defined, the crash dump code will not be compiled in.
//#define SMISK_NO_CRASH_REPORTING

// Chunk size for reading unknown length from a stream
#define SMISK_STREAM_READ_CHUNKSIZE 1024

// Default readline length for smisk.Stream.readline()
// Should probably match the buffer size lifcgi uses for 
// streams. See creation of NewReader or NewWriter in fcgiapp.c
#define SMISK_STREAM_READLINE_LENGTH 8192

// How much post data can be stored in memory instead of being written to disk
#define SMISK_POST_SIZE_MEMORY_LIMIT 10240000

// In case TEMPDIR is not present in env, this is used as a fallback.
// Must end with a slash.
// XXX todo windows incompatible
#define SMISK_FILE_UPLOAD_DIR "/tmp/"
// Prefix appended to temporary uploaded files:
#define SMISK_FILE_UPLOAD_PREFIX "smisk-upload-"

// Session ID compactness
// Warning: Changing SMISK_SESSION_NBITS may cause some smisk installations to
//          stop sharing sessions with each other, which is dangerous. Do not
//          change unless during a major version step.
#define SMISK_SESSION_NBITS 5

// Max size for form post data (x-www-form-urlencoded)
#define SMISK_FORM_DATA_MAX_SIZE 1024000000

// How to encode strs used for dict keys
#define SMISK_KEY_ENCODING "utf-8"

#endif
