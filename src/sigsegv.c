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

static void signal_segv(int signum, siginfo_t* info, void*ptr) {
    static const char *si_codes[3] = {"", "SEGV_MAPERR", "SEGV_ACCERR"};

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

    fprintf(stderr, "Segmentation Fault!\n");
    fprintf(stderr, "info.si_signo = %d\n", signum);
    fprintf(stderr, "info.si_errno = %d\n", info->si_errno);
    fprintf(stderr, "info.si_code  = %d (%s)\n", info->si_code, si_codes[info->si_code]);
    fprintf(stderr, "info.si_addr  = %p\n", info->si_addr);

#if defined(SIGSEGV_STACK_X86) || defined(SIGSEGV_STACK_IA64)
    ucontext_t *ucontext = (ucontext_t*)ptr;
    
    for(i = 0; i < NGREG; i++)
        fprintf(stderr, "reg[%02u]       = 0x" REGFORMAT "\n", i, ucontext->uc_mcontext.gregs[i]);
# if defined(SIGSEGV_STACK_IA64)
    ip = (void*)ucontext->uc_mcontext.gregs[REG_RIP];
    bp = (void**)ucontext->uc_mcontext.gregs[REG_RBP];
# elif defined(SIGSEGV_STACK_X86)
    ip = (void*)ucontext->uc_mcontext.gregs[REG_EIP];
    bp = (void**)ucontext->uc_mcontext.gregs[REG_EBP];
# endif

    fprintf(stderr, "Stack trace:\n");
    while(bp && ip) {
        if(!dladdr(ip, &dlinfo))
            break;

        const char *symname = dlinfo.dli_sname;

        fprintf(stderr, "% 2d: %p <%s+%u> (%s)\n",
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
    fprintf(stderr, "Stack trace (non-dedicated):\n");
    sz = backtrace(bt, 1000);
    strings = backtrace_symbols(bt, sz);
    size_t i;
    for(i = 0; i < sz; ++i)
        fprintf(stderr, "%s\n", strings[i]);
#endif
    fprintf(stderr, "End of stack trace\n");
    exit (-1);
}


int setup_sigsegv(void) {
    struct sigaction action;
    memset(&action, 0, sizeof(action));
    action.sa_sigaction = signal_segv;
    action.sa_flags = SA_SIGINFO;
    if(sigaction(SIGSEGV, &action, NULL) < 0) {
        perror("sigaction");
        return 0;
    }
    if(sigaction(SIGBUS, &action, NULL) < 0) {
        perror("sigaction");
        return 0;
    }
    
    return 1;
}

/*#ifndef SIGSEGV_NO_AUTO_INIT
static void __attribute((constructor)) init(void) {
    setup_sigsegv();
}
#endif*/
