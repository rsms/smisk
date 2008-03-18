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
#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include <memory.h>
#include <stdlib.h>
#include <stdio.h>
#include <signal.h>
#include <ucontext.h>
#include <dlfcn.h>
#include <execinfo.h>
/*#ifndef NO_CPP_DEMANGLE
#include <cxxabi.h>
#endif*/

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

void sigsegv_write_backtrace(siginfo_t* info, void*ptr, FILE *out) {
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

    if(dlinfo.dli_sname && !strcmp(dlinfo.dli_sname, "main"))
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

