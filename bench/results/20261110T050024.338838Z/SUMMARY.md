# FN-DSA — c-fn-dsa cross-check — QUICK

QUICK is a workflow check only. Full-scale figures are measured locally.

CPU: AMD EPYC 9V45 96-Core Processor; affinity: 0. GCC: gcc (Debian 14.2.0-19) 14.2.0.

Tested commit: `1b858880dcac091b5e5f84f0e4d8617c35ba1392`. Benchmark commit: `1b858880dcac091b5e5f84f0e4d8617c35ba1392`.

Base flags: `-O3 -march=native -std=gnu11`. Each operation: 11 iterations; correctness and lengths: 100 signatures per build/set. Message: 32 bytes. Median units: thousand RDTSC ticks.

Exact per-build options (in addition to base flags and local include paths):

* FN-DSA-512 ref: `-DLOGN=9 -DFNDSA_AVX2=0 -DFNDSA_SSE2=0 -DFNDSA_NEON=0 -ffunction-sections -fdata-sections -fno-tree-vectorize -fno-tree-slp-vectorize`; link `-Wl,--gc-sections`.
* FN-DSA-512 avx2: `-DLOGN=9 -DFNDSA_AVX2=1 -DFNDSA_SSE2=1 -DFNDSA_NEON=0 -ffunction-sections -fdata-sections -mavx2 -mno-avx512f`; link `-Wl,--gc-sections`.
* FN-DSA-1024 ref: `-DLOGN=10 -DFNDSA_AVX2=0 -DFNDSA_SSE2=0 -DFNDSA_NEON=0 -ffunction-sections -fdata-sections -fno-tree-vectorize -fno-tree-slp-vectorize`; link `-Wl,--gc-sections`.
* FN-DSA-1024 avx2: `-DLOGN=10 -DFNDSA_AVX2=1 -DFNDSA_SSE2=1 -DFNDSA_NEON=0 -ffunction-sections -fdata-sections -mavx2 -mno-avx512f`; link `-Wl,--gc-sections`.

| 参数集 | n | q | pk | sig（仓库实际） | 论文 sig | ref KeyGen/Sign/Verify | AVX2 KeyGen/Sign/Verify |
|---|---:|---:|---:|---|---:|---|---|
| FN-DSA-512 | 512 | 12289 | 897 | 666; unpadded avg 654.9100, max 661 | 666 | 7519.667/4676.437/41.053 | 4261.789/323.309/38.219 |
| FN-DSA-1024 | 1024 | 12289 | 1793 | 1280; unpadded avg 1270.7500, max 1278 | 1280 | 27354.859/9864.477/83.355 | 20959.353/634.581/56.757 |



Expanded-key Sign (thousand ticks; `--` means no supported expanded-key API):

| 参数集 | ref | AVX2 |
|---|---:|---:|
| FN-DSA-512 | -- | -- |
| FN-DSA-1024 | -- | -- |

Correctness: all configured upstream KAT/self-tests passed; all generated signatures verified; changed messages rejected. Cross-build/equality details are in correctness.json.

Cross-check implementation only; paper Falcon performance is from VecFalcon. This revision documents a 2026 best guess of future FIPS 206, not a published final standard. Compared with VecFalcon 61b326e: public keys are NTT encoded, encodings/hash-to-point are little-endian, signature infinity norm is capped at 840 instead of 2047, a 64-byte mu binds the hashed public key/context/message, secret keys include an additional 64-byte public-key hash, the base sampler uses 79 bits rather than 72, and SHAKE256x4 was removed. It is not a drop-in original round-3 Falcon implementation or interoperable wire format with the earlier VecFalcon API, despite the same public-key/signature lengths. Signatures remain padded 666/1280 bytes; exact unpadding parses the LSB-first compressed polynomial and checks against comp_decode. The scalar ref disables SIMD and uses software binary64, AVX2 uses native SIMD/FPU. Native degree-specific transcript KATs are mandatory for both. Public C API exposes only encoded keys; ExpandedSign is unavailable.

Build flags and commands per variant are in config.json, metadata.json and build logs. All source is extracted locally from the tested commit; algorithm files are unchanged. See bench/NOTES.md.
