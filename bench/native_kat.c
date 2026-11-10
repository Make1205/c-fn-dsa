#define main unused_upstream_main
#include "../test_fndsa.c"
#undef main
int main(void){
#if LOGN == 9
inner_test_kat(9,KAT_512);
#else
inner_test_kat(10,KAT_1024);
#endif
puts("PASS native KAT");return 0;}
