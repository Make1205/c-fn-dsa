
Verify diagnostic split (thousand TSC ticks; instrumented, separate from the main Verify metric):

| Set | Build | vzeroupper before call | PK decode/preparation | Remaining core | Instrumented total | CPU dispatch (included in core) |
|---|---|---|---:|---:|---:|---:|
| FN-DSA-512 | ref | False | 1.325 | 34.319 | 35.645 | 0.000 |
| FN-DSA-512 | avx2 | False | 1.143 | 52.779 | 54.027 | 23.087 |
| FN-DSA-512 | avx2 | True | 1.273 | 56.237 | 57.511 | 24.465 |
| FN-DSA-1024 | ref | False | 2.391 | 65.571 | 67.963 | 0.000 |
| FN-DSA-1024 | avx2 | False | 2.313 | 84.317 | 86.605 | 23.997 |
| FN-DSA-1024 | avx2 | True | 2.287 | 84.031 | 86.319 | 24.543 |

PK phase brackets original mqpoly_decode through initial representation conversion; this version stores PK in NTT wire format, so no PK NTT is performed. Core is the same-sample remainder, including PK/message hashing, dispatch, signature decoding and verification arithmetic. Linker hooks add boundary overhead; these diagnostic medians do not replace the main public API median, and medians need not add. The clean probe inserts only vzeroupper before the timed API. Static ISA counts are in *-isa.json.

Sign diagnostic (encoded-key API, fixed seed corpus; not a replacement for the main timing):

| Set | Build | Instrumented Sign kcycles | CPU detection kcycles | Mean detection calls/sign | Max |
|---|---|---:|---:|---:|---:|
| FN-DSA-512 | ref | 436.097 | 0.000 | 0.0000 | 0 |
| FN-DSA-512 | avx2 | 424.085 | 0.000 | 0.0000 | 0 |
| FN-DSA-1024 | ref | 889.797 | 0.000 | 0.0000 | 0 |
| FN-DSA-1024 | avx2 | 843.153 | 0.000 | 0.0000 | 0 |
