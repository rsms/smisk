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
#include "version.h"
#include "__init__.h"
#include "Application.h"
#include "Request.h"
#include "Response.h"
#include "Stream.h"
#include "URL.h"
#include "SessionStore.h"
#include "FileSessionStore.h"
#include "xml/__init__.h"
#ifndef SMISK_NO_CRASH_REPORTING
#include "sigsegv.h"
#endif

#include <fastcgi.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <sys/un.h>
#include <arpa/inet.h>
#include <signal.h>
#include <unistd.h>

#if HAVE_SYS_UTSNAME_H
#include <sys/utsname.h>
#endif
#include <fcgiapp.h>
#include <fastcgi.h>

// Set default listensock
int smisk_listensock_fileno = FCGI_LISTENSOCK_FILENO;

// Objects at module-level
PyObject *smisk_Error, *smisk_IOError, *smisk_InvalidSessionError;
PyObject *os_module;

// Other static strings (only used in C API)
PyObject *kString_http;
PyObject *kString_https;


#ifndef SMISK_NO_CRASH_REPORTING
  static void smisk_crash_sighandler(int signum, siginfo_t* info, void*ptr) {
    FILE *out = NULL;
    char out_fn[PATH_MAX];
    char cwd_buf[PATH_MAX];
    char *cwd = NULL;
    struct tm *t;
    time_t timer;
    size_t i = 0;
    const char *found_gdb_path;
    char cmd[1024];
    // Signal code table (from http://www.opengroup.org/onlinepubs/007908799/xsh/signal.h.html)
    static const char *si_codes[][9] = {
      {"", "", "", "", "", "", "", "", ""},
      {"", "", "", "", "", "", "", "", ""},
      {"", "", "", "", "", "", "", "", ""},
      {"",
       "ILL_ILLOPC\tillegal opcode",
       "ILL_ILLOPN\tillegal operand",
       "ILL_ILLADR\tillegal addressing mode",
       "ILL_ILLTRP\tillegal trap",
       "ILL_PRVOPC\tprivileged opcode",
       "ILL_PRVREG\tprivileged register",
       "ILL_COPROC\tcoprocessor error",
       "ILL_BADSTK\tinternal stack error"}, // ILL
      {"", "", "", "", "", "", "", "", ""},
      {"", "", "", "", "", "", "", "", ""},
      {"", "", "", "", "", "", "", "", ""},
      {"",
       "FPE_INTDIV\tinteger divide by zero",
       "FPE_INTOVF\tinteger overflow", 
       "FPE_FLTDIV\tfloating point divide by zero",
       "FPE_FLTOVF\tfloating point overflow",
       "FPE_FLTUND\tfloating point underflow",
       "FPE_FLTRES\tfloating point inexact result",
       "FPE_FLTINV\tinvalid floating point operation",
       "FPE_FLTSUB\tsubscript out of range"}, // FPE
      {"", "", "", "", "", "", "", "", ""},
      {"",
       "BUS_ADRALN\tinvalid address alignment",
       "BUS_ADRERR\tnon-existent physical address",
       "BUS_OBJERR\tobject specific hardware error",
       "", "", "", ""}, // BUS
      {"",
       "SEGV_MAPERR\taddress not mapped to object",
       "SEGV_ACCERR\tinvalid permissions for mapped object",
       "", "", "", "", "", ""} // SEGV
    };
    // Possible paths to GDB
    static const char *gdb_path[] = {
      "/usr/bin/gdb",
      "/usr/local/bin/gdb",
      "/opt/local/bin/gdb",
      "/opt/bin/gdb",
      "/local/bin/gdb",
      NULL
    };
    
    // Header
    fprintf(stderr, "FATAL: smisk died from signal %d (%s). ", // intentionally no LF
      signum, (signum == SIGSEGV) ? "Segmentation violation" : "Bus error");
    fflush(stderr);
    
    // Construct filename smisk-YYYYMMDD-HHMMSS.PID.crash
    timer = time(NULL);
    t = localtime(&timer);
    cwd = getcwd(cwd_buf, PATH_MAX);
    sprintf(out_fn, "%s/smisk-%04d%02d%02d-%02d%02d%02d.%d.crash",
      (access(cwd ? cwd : ".", W_OK) == 0) ? (cwd ? cwd : ".") : "/tmp",
      1900+t->tm_year, t->tm_mon+1, t->tm_mday, t->tm_hour, t->tm_min, t->tm_sec, getpid());
    
    // Open file
    fprintf(stderr, "Writing crash dump to %s...\n", out_fn);
    out = fopen(out_fn, "w");
    if(!out)
      out = stderr;
    
    // Basic info
    fprintf(out, "Time:               %04d-%02d-%02d %02d:%02d:%02d\n",
      1900+t->tm_year, t->tm_mon+1, t->tm_mday, t->tm_hour, t->tm_min, t->tm_sec);
    fprintf(out, "Process:            %d\n", getpid());
    fprintf(out, "Working directory:  %s\n", cwd ? cwd : "?");
    fprintf(out, "Python:             %s %s\n", Py_GetProgramFullPath(), Py_GetVersion());
    fprintf(out, "Smisk:              %s (r%s %s %s)\n", SMISK_VERSION, SMISK_REVISION, __DATE__, __TIME__);
    #if HAVE_SYS_UTSNAME_H
      struct utsname un;
      if(uname(&un) == 0) {
        fprintf(out, "System:             %s, %s, %s, %s\n",
          un.sysname, un.release, un.version, un.machine);
        fprintf(out, "Hostname:           %s\n", un.nodename);
      }
      else
    #endif
      fprintf(out, "System:             %s\n", Py_GetPlatform());
    fprintf(out, "\n");
    fprintf(out, "Signal:             %d\n", signum);
    fprintf(out, "Errno:              %d\n", info->si_errno);
    fprintf(out, "Code:               %d\t%s\n", info->si_code, (signum > 0) ? si_codes[signum-1][info->si_code] : "?");
    fprintf(out, "Address:            %p\n", info->si_addr);
    
    // Find GDB
    i = 0;
    found_gdb_path = NULL;
    do {
      if(access(*(gdb_path+i), R_OK) == 0) {
        found_gdb_path = *(gdb_path+i);
        log_debug("found gdb at %s", found_gdb_path);
        break;
      }
    } while ( *(gdb_path + ++i) );
    
    // Write backtrace
    fprintf(out, "\nBacktrace:\n");
    if(found_gdb_path) {
      fclose(out);
      system("/bin/echo 'backtrace' > /tmp/smisk_gdb_args");
      sprintf(cmd, "%s -batch -x /tmp/smisk_gdb_args %s %d >> %s",
        found_gdb_path, Py_GetProgramFullPath(), getpid(), out_fn);
      system(cmd);
    }
    else {
      log_error("Note: GDB not found. Install GDB to get a more detailed backtrace.");
      sigsegv_write_backtrace(info, ptr, out);
      fclose(out);
    }
    
    //exit(-1);
    _exit(-1);
  }
  
  static void smisk_crash_dump_init(void) {
    struct sigaction action;
    memset(&action, 0, sizeof(action));
    action.sa_sigaction = smisk_crash_sighandler;
    action.sa_flags = SA_SIGINFO;
    // Important: Only register for signals which have
    //            its codes in the si_codes table above.
    if(sigaction(SIGILL, &action, NULL) < 0) {
      perror("sigaction"); return;
    }
    if(sigaction(SIGFPE, &action, NULL) < 0) {
      perror("sigaction"); return;
    }
    if(sigaction(SIGBUS, &action, NULL) < 0) {
      perror("sigaction"); return;
    }
    if(sigaction(SIGSEGV, &action, NULL) < 0) {
      perror("sigaction");
    }
  }
#else
  #define smisk_crash_dump_init()
#endif


PyDoc_STRVAR(smisk_bind_DOC,
  "Bind to a specific unix socket or host (and/or port).\n"
  "\n"
  ":param path: The Unix domain socket (named pipe for WinNT), hostname, "
    "hostname and port or just a colon followed by a port number. e.g. "
    "\"/tmp/fastcgi/mysocket\", \"some.host:5000\", \":5000\", \"\\*:5000\".\n"
  ":type  path: string\n"
  ":param backlog: The listen queue depth used in the ''listen()'' call. "
    "Set to negative or zero to let the system decide (recommended).\n"
  ":type  backlog: int\n"
  ":raises smisk.IOError: On failure.\n"
  ":rtype: None");
PyObject* smisk_bind(PyObject *self, PyObject *args) {
  //int FCGX_OpenSocket(const char *path, int backlog)
  int fd, backlog;
  PyObject* path;
  
  // Set default backlog size (<=0 = let system implementation decide)
  backlog = 0;
  
  // Did we get enough arguments?
  if(!args || PyTuple_GET_SIZE(args) < 1) {
    PyErr_SetString(PyExc_TypeError, "bind takes at least 1 argument");
    return NULL;
  }
  
  // Save reference to first argument and type check it
  path = PyTuple_GET_ITEM(args, 0);
  if(path == NULL || !PyString_Check(path)) {
    PyErr_SetString(PyExc_TypeError, "first argument must be a string");
    return NULL;
  }
  
  // Did we get excplicit backlog size?
  if(PyTuple_GET_SIZE(args) > 1) {
    PyObject* arg1 = PyTuple_GET_ITEM(args, 1);
    if(arg1 != NULL) {
      if(!PyInt_Check(arg1)) {
        PyErr_SetString(PyExc_TypeError, "second argument must be an integer");
        return NULL;
      }
      backlog = (int)PyInt_AS_LONG(arg1);
    }
  }
  
  // Bind/listen
  fd = FCGX_OpenSocket(PyString_AS_STRING(path), backlog);
  if(fd < 0) {
    log_debug("ERROR: FCGX_OpenSocket(\"%s\", %d) returned %d. errno: %d", 
      PyString_AS_STRING(path), backlog, fd, errno);
    return PyErr_SET_FROM_ERRNO;
  }
  
  // Set the process global fileno
  smisk_listensock_fileno = fd;
  
  Py_RETURN_NONE;
}


PyDoc_STRVAR(smisk_listening_DOC,
  "Find out if this process is a \"remote\" process, bound to a socket "
  "by means of calling bind(). If it is listening, this function returns "
  "the address and port or the UNIX socket path. If not bound, this "
  "function returns None.\n"
  "\n"
  ":raises smisk.IOError: On failure.\n"
  ":rtype: string");
PyObject* smisk_listening(PyObject *self, PyObject *args) {
  PyObject *s = Py_None;
  socklen_t addrlen;
  struct sockaddr *addr;
  
  if(smisk_listensock_fileno == FCGI_LISTENSOCK_FILENO) {
    Py_RETURN_NONE;
  }
  
  addrlen = sizeof(struct sockaddr_in); // Assume INET
  addr = (struct sockaddr *)malloc(addrlen);
  if(getsockname(smisk_listensock_fileno, addr, &addrlen) != 0) {
    return PyErr_SET_FROM_ERRNO;
  }
  
  if(addr->sa_family == AF_INET || addr->sa_family == AF_INET6) {
    char *saddr = "*";
    if(((struct sockaddr_in *)addr)->sin_addr.s_addr != (in_addr_t)0) {
      saddr = (char *)inet_ntoa(((struct sockaddr_in *)addr)->sin_addr);
    }
    s = PyString_FromFormat("%s:%d",
      saddr, 
      htons(((struct sockaddr_in *)addr)->sin_port) );
  }
  else if(addr->sa_family == AF_UNIX) {
    // This may be a bit risky...
    s = PyString_FromString(((struct sockaddr_un *)addr)->sun_path);
  }
  
  if(s == Py_None) {
    Py_INCREF(s);
  }
  return s;
}

/* ------------------------------------------------------------------------- */

static PyMethodDef module_methods[] = {
  {"bind",      (PyCFunction)smisk_bind,       METH_VARARGS, smisk_bind_DOC},
  {"listening", (PyCFunction)smisk_listening,  METH_NOARGS,  smisk_listening_DOC},
  {NULL, NULL, 0, NULL}
};

PyDoc_STRVAR(smisk_module_DOC,
  "Smisk core library");

PyMODINIT_FUNC initcore(void) {
  PyObject* module;
  module = Py_InitModule("smisk.core", module_methods);
  
  // Seed random
  srandom((unsigned int)getpid());
  
  // Initialize crash dumper
  smisk_crash_dump_init();
  
  // Load os module
  PyObject *os_str = PyString_FromString("os");
  os_module = PyImport_Import(os_str);
  Py_DECREF(os_str);
  if(os_module == NULL) {
    return;
  }
  
  // Constants: Other static strings (only used in C API)
  kString_http = PyString_FromString("http");
  kString_https = PyString_FromString("https");
  
  // Constants: Special variables
  if(PyModule_AddStringConstant(module, "__version__", SMISK_VERSION) != 0) return;
  if(PyModule_AddStringConstant(module, "__build__", SMISK_REVISION) != 0) return;
  if(PyModule_AddStringConstant(module, "__doc__", smisk_module_DOC) != 0) return;
  
  // Register types
  if (!module ||
    (smisk_Application_register_types(module) != 0) ||
    (smisk_Request_register_types(module) != 0) ||
    (smisk_Response_register_types(module) != 0) ||
    (smisk_Stream_register_types(module) != 0) ||
    (smisk_URL_register_types(module) != 0) ||
    (smisk_SessionStore_register_types(module) != 0) ||
    (smisk_FileSessionStore_register_types(module) != 0) ||
    (smisk_xml_register(module) == NULL)
    ) {
      return;
  }
  
  // Exceptions
  if (!(smisk_Error = PyErr_NewException("smisk.core.Error", PyExc_StandardError, NULL))) return;
  PyModule_AddObject(module, "Error", smisk_Error);
  if (!(smisk_IOError = PyErr_NewException("smisk.core.IOError", PyExc_IOError, NULL))) return;
  PyModule_AddObject(module, "IOError", smisk_IOError);
  if (!(smisk_InvalidSessionError = PyErr_NewException("smisk.core.InvalidSessionError", PyExc_ValueError, NULL))) return;
  PyModule_AddObject(module, "InvalidSessionError", smisk_InvalidSessionError);
}

