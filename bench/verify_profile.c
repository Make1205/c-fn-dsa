/* Bench-only linker hooks; original algorithm translation units are unchanged. */
#define main unused_benchmark_main
#include "driver.c"
#undef main
#ifndef BENCH_PK_NTT
#define BENCH_PK_NTT 0
#endif
static volatile int pf_active;
static uint64_t pf_begin,pf_end,pf_dispatch;
static unsigned pf_decode_calls,pf_ext_calls,pf_ntt_calls,pf_cpu_calls;
extern size_t __real_fndsa_mqpoly_decode(unsigned,const uint8_t*,uint16_t*);
size_t __wrap_fndsa_mqpoly_decode(unsigned logn,const uint8_t *s,uint16_t *h){
 if(pf_active==1){pf_decode_calls++;pf_begin=cpucycles();}
 return __real_fndsa_mqpoly_decode(logn,s,h);
}
extern void __real_fndsa_mqpoly_ext_to_int(unsigned,uint16_t*);
void __wrap_fndsa_mqpoly_ext_to_int(unsigned logn,uint16_t*d){
 __real_fndsa_mqpoly_ext_to_int(logn,d);
 if(pf_active==1&&++pf_ext_calls==1&&!BENCH_PK_NTT)pf_end=cpucycles();
}
#if BENCH_PK_NTT
extern void __real_fndsa_mqpoly_int_to_ntt(unsigned,uint16_t*);
void __wrap_fndsa_mqpoly_int_to_ntt(unsigned logn,uint16_t*d){
 __real_fndsa_mqpoly_int_to_ntt(logn,d);
 if(pf_active==1&&++pf_ntt_calls==1)pf_end=cpucycles();
}
#endif
#if FNDSA_AVX2
extern void __real_fndsa_avx2_mqpoly_ext_to_int(unsigned,uint16_t*);
void __wrap_fndsa_avx2_mqpoly_ext_to_int(unsigned logn,uint16_t*d){
 __real_fndsa_avx2_mqpoly_ext_to_int(logn,d);
 if(pf_active==1&&++pf_ext_calls==1&&!BENCH_PK_NTT)pf_end=cpucycles();
}
#if BENCH_PK_NTT
extern void __real_fndsa_avx2_mqpoly_int_to_ntt(unsigned,uint16_t*);
void __wrap_fndsa_avx2_mqpoly_int_to_ntt(unsigned logn,uint16_t*d){
 __real_fndsa_avx2_mqpoly_int_to_ntt(logn,d);
 if(pf_active==1&&++pf_ntt_calls==1)pf_end=cpucycles();
}
#endif
extern int __real_fndsa_has_avx2(void);
int __wrap_fndsa_has_avx2(void){
 if(!pf_active)return __real_fndsa_has_avx2();
 uint64_t a=cpucycles();int r=__real_fndsa_has_avx2();pf_dispatch+=cpucycles()-a;pf_cpu_calls++;return r;
}
#endif
int main(int argc,char **argv){
 must(argc==2||argc==3,"verify_profile count [clean]");unsigned count=(unsigned)strtoul(argv[1],0,10);must(count>0,"count");
 int clean=argc==3&&!strcmp(argv[2],"clean");bench_testing=1;bench_seed(1234567);
 uint64_t *total=calloc(count+1,8),*prep=calloc(count+1,8),*core=calloc(count+1,8),*dispatch=calloc(count+1,8);must(total&&prep&&core&&dispatch,"profile allocation");
 for(unsigned i=0;i<count+20;i++){
  must(!b_keygen(pk,sk),"profile keygen");sign_one();
#if FNDSA_AVX2
  if(clean)_mm256_zeroupper();
#else
  must(!clean,"clean probe requires AVX2 build");
#endif
  pf_begin=pf_end=pf_dispatch=0;pf_decode_calls=pf_ext_calls=pf_ntt_calls=pf_cpu_calls=0;pf_active=1;
  uint64_t a=cpucycles();int rc=b_verify(sig,slen,msg,32,pk);uint64_t dt=cpucycles()-a;pf_active=0;
  must(!rc,"profile verification");must(pf_decode_calls==1&&pf_begin&&pf_end>=pf_begin,"pk hooks");
  uint64_t pd=pf_end-pf_begin;must(dt>=pd,"profile intervals");
  if(i>=20){unsigned j=i-20;total[j+1]=total[j]+dt;prep[j+1]=prep[j]+pd;core[j+1]=core[j]+dt-pd;dispatch[j+1]=dispatch[j]+pf_dispatch;}
 }
 printf("PROFILE_META %u %d %d %u %u %u %u\n",count,clean,BENCH_PK_NTT,pf_decode_calls,pf_ext_calls,pf_ntt_calls,pf_cpu_calls);
 print_results("PKDecode",prep,count+1);print_results("CoreVerify",core,count+1);print_results("VerifyInstrumented",total,count+1);
 if(pf_cpu_calls)print_results("DispatchDetect",dispatch,count+1);
 if(!clean){
  memset(total,0,(count+1)*8);memset(dispatch,0,(count+1)*8);unsigned long long calls=0;unsigned max_calls=0;
  for(unsigned i=0;i<count+20;i++){
   must(!b_keygen(pk,sk),"sign profile keygen");slen=B_SIG;pf_dispatch=0;pf_cpu_calls=0;pf_active=2;
   uint64_t a=cpucycles();int rc=b_sign(sig,&slen,msg,32,sk);uint64_t dt=cpucycles()-a;pf_active=0;
   must(!rc&&!b_verify(sig,slen,msg,32,pk),"sign profile verification");
   if(i>=20){unsigned j=i-20;total[j+1]=total[j]+dt;dispatch[j+1]=dispatch[j]+pf_dispatch;calls+=pf_cpu_calls;if(pf_cpu_calls>max_calls)max_calls=pf_cpu_calls;}
  }
  print_results("SignInstrumented",total,count+1);if(calls)print_results("SignDispatchDetect",dispatch,count+1);
  printf("SIGN_DISPATCH_CALLS %llu %u %u\n",calls,max_calls,count);
 }
 free(total);free(prep);free(core);free(dispatch);return 0;
}
