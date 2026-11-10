#ifndef BENCH_ADAPTER_H
#define BENCH_ADAPTER_H
#include "fndsa.h"
#include "inner.h"
#define B_N (1<<LOGN)
#define B_Q 12289
#define B_PK FNDSA_VRFY_KEY_SIZE(LOGN)
#define B_SK FNDSA_SIGN_KEY_SIZE(LOGN)
#define B_SIG FNDSA_SIGNATURE_SIZE(LOGN)
extern int bench_testing;
void bench_fill(void*,size_t);
static int b_keygen(uint8_t*p,uint8_t*s){if(bench_testing){uint8_t seed[40];bench_fill(seed,32);fndsa_keygen_seeded(LOGN,seed,32,s,p);return 0;}return !fndsa_keygen(LOGN,s,p);}
static int b_sign(uint8_t*s,size_t*l,const uint8_t*m,size_t n,const uint8_t*k){if(bench_testing){uint8_t seed[40];bench_fill(seed,40);*l=fndsa_sign_seeded(k,B_SK,0,0,FNDSA_HASH_ID_RAW,m,n,seed,40,s,B_SIG);}else *l=fndsa_sign(k,B_SK,0,0,FNDSA_HASH_ID_RAW,m,n,s,B_SIG);return *l==0;}
static int b_verify(const uint8_t*s,size_t l,const uint8_t*m,size_t n,const uint8_t*k){return !fndsa_verify(s,l,k,B_PK,0,0,FNDSA_HASH_ID_RAW,m,n);}
static size_t b_unpadded(const uint8_t*s,size_t n){size_t bit=41*8;for(int i=0;i<B_N;i++){bit+=8;for(;;){if(bit>=n*8)return 0;unsigned v=(s[bit/8]>>(bit%8))&1;bit++;if(v)break;}}int16_t d[B_N];if(!comp_decode(LOGN,s+41,n-41,d))return 0;size_t exp=41*8;for(int i=0;i<B_N;i++){int x=d[i];unsigned a=x<0?-x:x;exp+=9+(a>>7);}return (exp+7)/8==(bit+7)/8?(bit+7)/8:0;}
#endif
