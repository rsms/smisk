/**
 * This source file is used to print out a stack-trace when your program
 * segfaults.  It is relatively reliable and spot-on accurate.
 *
 * This code is in the public domain.  Use it as you see fit, some credit
 * would be appreciated, but is not a prerequisite for usage.  Feedback
 * on it's use would encourage further development and maintenance.
 *
 * Author:  Jaco Kroon <jaco@kroon.co.za>
 *
 * Copyright (C) 2005 - 2006 Jaco Kroon
 */
#ifndef SMISK_NO_CRASH_REPORTING

#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include "crash_dump.h"
#include <memory.h>
#include <stdlib.h>
#include <ucontext.h>
#include <dlfcn.h>
#include <execinfo.h>
#include <signal.h>
#include <stdio.h>
#if HAVE_SYS_UTSNAME_H
#include <sys/utsname.h>
#endif

#if defined(REG_RIP)
  #define SIGSEGV_STACK_IA64
  #define REGFORMAT "%016lx"
#elif defined(REG_EIP)
  #define SIGSEGV_STACK_X86
  #define REGFORMAT "%08x"
#else
  #define SIGSEGV_STACK_GENERIC
  #define REGFORMAT "%x"
#endif

static void smisk_crash_write_backtrace(siginfo_t *info, void *ptr, FILE *out) {
  size_t i;
  
#if defined(SIGSEGV_STACK_X86) || defined(SIGSEGV_STACK_IA64)
  int f = 0;
  Dl_info dlinfo;
  void **bp = 0;
  void *ip = 0;
#else
  void *bt[20];
  char **strings;
  size_t sz;
#endif

#if defined(SIGSEGV_STACK_X86) || defined(SIGSEGV_STACK_IA64)
  ucontext_t *ucontext = (ucontext_t*)ptr;
  
  for(i = 0; i < NGREG; i++)
    fprintf(out, "reg[%02lu]     = 0x" REGFORMAT "\n", i, (unsigned long)ucontext->uc_mcontext.gregs[i]);
# if defined(SIGSEGV_STACK_IA64)
  ip = (void*)ucontext->uc_mcontext.gregs[REG_RIP];
  bp = (void**)ucontext->uc_mcontext.gregs[REG_RBP];
# elif defined(SIGSEGV_STACK_X86)
  ip = (void*)ucontext->uc_mcontext.gregs[REG_EIP];
  bp = (void**)ucontext->uc_mcontext.gregs[REG_EBP];
# endif

  fprintf(out, "Stack trace:\n");
  while(bp && ip) {
    if(!dladdr(ip, &dlinfo))
      break;

    const char *symname = dlinfo.dli_sname;

    fprintf(out, "% 2d: %p <%s+%u> (%s)\n",
        ++f,
        ip,
        symname,
        (unsigned)(ip - dlinfo.dli_saddr),
        dlinfo.dli_fname);

    if(dlinfo.dli_sname && smisk_str4cmp(dlinfo.dli_sname, 'm','a','i','n'))
      break;

    ip = bp[1];
    bp = (void**)bp[0];
  }
#else
  fprintf(out, "Stack trace (non-dedicated):\n");
  sz = backtrace(bt, 1000);
  strings = backtrace_symbols(bt, sz);
  for(i = 0; i < sz; ++i)
    fprintf(out, "%s\n", strings[i]);
#endif
  fprintf(out, "End of stack trace\n");
}


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
  fputs("FATAL: smisk died from ", stderr);
  switch(signum) {
    case SIGILL:
      fputs("Illegal instruction ", stderr);
      break;
    case SIGFPE:
      fputs("Floating-point exception ", stderr);
      break;
    case SIGBUS:
      fputs("Bus error ", stderr);
      break;
    case SIGSEGV:
      fputs("Segmentation violation ", stderr);
      break;
  }
  fprintf(stderr, "[%d] ", signum);
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
  fprintf(out, "Smisk:              %s (%s)\n", SMISK_VERSION, SMISK_BUILD_ID);
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
    smisk_crash_write_backtrace(info, ptr, out);
    fclose(out);
  }
  
  //exit(-1);
  _exit(-1);
}

void smisk_crash_dump_init(void) {
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

#else /* SMISK_NO_CRASH_REPORTING */
void smisk_crash_dump_init(void) {}
#endif
