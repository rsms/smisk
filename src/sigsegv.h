#ifndef __SIGSEGV_H__
#define __SIGSEGV_H__

void sigsegv_write_backtrace (siginfo_t* info, void *ptr, FILE *out);

#endif
