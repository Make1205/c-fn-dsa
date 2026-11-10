# Falcon primary — c-fn-dsa (pre-standard FN-DSA) — QUICK

QUICK is a workflow check only. Full-scale figures are measured locally.

CPU: AMD EPYC 9V74 80-Core Processor; affinity: 0. GCC: gcc (Debian 14.2.0-19) 14.2.0.

Tested commit: `1b858880dcac091b5e5f84f0e4d8617c35ba1392`. Benchmark commit: `f105a453c95b7cf0626b4664623bcba1dd785b24`.

Base flags: `-O3 -march=native -std=c99 -D_DEFAULT_SOURCE -ffp-contract=off`. Each operation: 11 iterations; correctness and lengths: 100 signatures per build/set. Message: 32 bytes. Median units: thousand RDTSC ticks.

Ref backend: Upstream SSE2 hardware binary64, FNDSA_AVX2=0, FNDSA_SSE2=1; not a pure-C no-intrinsics backend (none exists on x86 in this source).

Timing sample population: fresh KeyGen/Sign/Verify triple per round, 20 discarded warmup triples; upstream OS entropy.

Exact per-build options (in addition to base flags and local include paths):

* FN-DSA-512 ref: `-DLOGN=9 -DFNDSA_AVX2=0 -DFNDSA_SSE2=1 -DFNDSA_NEON=0 -ffunction-sections -fdata-sections -msse2 -mno-avx -mno-avx2 -mno-avx512f -mno-fma`; link `-Wl,--gc-sections`.
* FN-DSA-512 avx2: `-DLOGN=9 -DFNDSA_AVX2=1 -DFNDSA_SSE2=1 -DFNDSA_NEON=0 -ffunction-sections -fdata-sections -mavx2 -mno-avx512f`; link `-Wl,--gc-sections`.
* FN-DSA-512 soft: `-DLOGN=9 -DFNDSA_AVX2=0 -DFNDSA_SSE2=0 -DFNDSA_NEON=0 -ffunction-sections -fdata-sections -mno-avx -mno-avx2 -mno-avx512f -mno-fma`; link `-Wl,--gc-sections`.
* FN-DSA-1024 ref: `-DLOGN=10 -DFNDSA_AVX2=0 -DFNDSA_SSE2=1 -DFNDSA_NEON=0 -ffunction-sections -fdata-sections -msse2 -mno-avx -mno-avx2 -mno-avx512f -mno-fma`; link `-Wl,--gc-sections`.
* FN-DSA-1024 avx2: `-DLOGN=10 -DFNDSA_AVX2=1 -DFNDSA_SSE2=1 -DFNDSA_NEON=0 -ffunction-sections -fdata-sections -mavx2 -mno-avx512f`; link `-Wl,--gc-sections`.
* FN-DSA-1024 soft: `-DLOGN=10 -DFNDSA_AVX2=0 -DFNDSA_SSE2=0 -DFNDSA_NEON=0 -ffunction-sections -fdata-sections -mno-avx -mno-avx2 -mno-avx512f -mno-fma`; link `-Wl,--gc-sections`.

| 参数集 | n | q | pk | sig（仓库实际） | 论文 sig | ref KeyGen/Sign/Verify | AVX2 KeyGen/Sign/Verify |
|---|---:|---:|---:|---|---:|---|---|
| FN-DSA-512 | 512 | 12289 | 897 | 666; unpadded avg 654.9100, max 661 | 666 | 9391.199/444.885/35.567 | 5618.235/426.841/53.506 |
| FN-DSA-1024 | 1024 | 12289 | 1793 | 1280; unpadded avg 1270.7500, max 1278 | 1280 | 31756.737/882.621/67.885 | 19059.403/877.342/85.643 |



Expanded-key Sign (thousand ticks; `--` means no supported expanded-key API):

| 参数集 | ref | AVX2 |
|---|---:|---:|
| FN-DSA-512 | -- | -- |
| FN-DSA-1024 | -- | -- |

Supplemental software binary64 (not the main ref; thousand ticks):

| 参数集 | soft KeyGen/Sign/Verify |
|---|---|
| FN-DSA-512 | 9843.625/6931.365/47.995 |
| FN-DSA-1024 | 47062.807/13891.695/93.417 |

Actual encoded length by backend (internal encoding parser; padding excluded):

| 参数集 | Backend | Samples | Mean bytes | Max bytes |
|---|---|---:|---:|---:|
| FN-DSA-512 | ref | 100 | 654.9100 | 661 |
| FN-DSA-512 | avx2 | 100 | 654.9100 | 661 |
| FN-DSA-512 | soft | 100 | 654.9100 | 661 |
| FN-DSA-1024 | ref | 100 | 1270.7500 | 1278 |
| FN-DSA-1024 | avx2 | 100 | 1270.7500 | 1278 |
| FN-DSA-1024 | soft | 100 | 1270.7500 | 1278 |

Byte equality diagnostics (differences do not waive cross-verification):

| 参数集 | Backend pair | Equal | Differing signatures | First differing sample (1-based) |
|---|---|---|---:|---:|
| FN-DSA-512 | ref / avx2 | True | 0 | -- |
| FN-DSA-512 | ref / soft | True | 0 | -- |
| FN-DSA-512 | avx2 / soft | True | 0 | -- |
| FN-DSA-1024 | ref / avx2 | True | 0 | -- |
| FN-DSA-1024 | ref / soft | True | 0 | -- |
| FN-DSA-1024 | avx2 / soft | True | 0 | -- |

All ordered backend cross-verification pairs passed, including the supplemental software backend. First-difference signatures, seeds, message, offsets and hashes are retained under diagnostics/ when a difference occurs.

Correctness: all configured upstream KAT/self-tests passed; all generated signatures verified; changed messages rejected. Cross-build/equality details are in correctness.json.


FMA audit: compiler contraction disabled; zero FMA instructions in every linked driver and benchmark-owned object. See *-fma-audit.json.
Cross-check implementation only; paper Falcon performance is from VecFalcon. This revision documents a 2026 best guess of future FIPS 206, not a published final standard. Compared with VecFalcon 61b326e: public keys are NTT encoded, encodings/hash-to-point are little-endian, signature infinity norm is capped at 840 instead of 2047, a 64-byte mu binds the hashed public key/context/message, secret keys include an additional 64-byte public-key hash, the base sampler uses 79 bits rather than 72, and SHAKE256x4 was removed. It is not a drop-in original round-3 Falcon implementation or interoperable wire format with the earlier VecFalcon API, despite the same public-key/signature lengths. Signatures remain padded 666/1280 bytes; exact unpadding parses the LSB-first compressed polynomial and checks against comp_decode. The scalar ref disables SIMD and uses software binary64, AVX2 uses native SIMD/FPU. Native degree-specific transcript KATs are mandatory for both. Public C API exposes only encoded keys; ExpandedSign is unavailable. Revision 2026-11-10: c-fn-dsa is primary and VecFalcon backup. Main ref now uses upstream SSE2 hardware binary64 with AVX2 disabled; it contains SSE2 intrinsics and is not a pure-C portable double path. The source has no FALCON_FPNATIVE switch. Software binary64 is supplemental only. GCC -O3 -march=native plus backend-required options; byte keys, 32-byte messages, fresh key/sign/verify triples, 20 warmup triples and unchanged Dilithium timing files. Every backend pair cross-verifies; equality and first differences are recorded separately. Original local FULL mismatch evidence remains pending until the original vectors are inspected. Current rule: -ffp-contract=off mandatory for all variants; runtime object/executable FMA audit must be zero. c-fn-dsa is primary, VecFalcon backup.

Build flags and commands per variant are in config.json, metadata.json and build logs. All source is extracted locally from the tested commit; algorithm files are unchanged. See bench/NOTES.md.
