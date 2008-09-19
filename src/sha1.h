#ifndef SHA1_H
#define SHA1_H

typedef struct {
    unsigned long state[5];
    unsigned long count[2];
    byte buffer[64];
} sha1_ctx_t;

void sha1_init (sha1_ctx_t* context);
void sha1_update (sha1_ctx_t* context, byte* data, unsigned int len);
void sha1_final (sha1_ctx_t* context, byte digest[20]);

void sha1_transform (unsigned long state[5], byte buffer[64]);

#endif
