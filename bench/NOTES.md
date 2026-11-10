# Benchmark notes

Initial worktree: clean. `bench` was created from the recorded initial commit.
Only files under `bench/` are added. Algorithm source, parameters and original
build files remain unchanged. The runner extracts the selected commit with local
`git archive`, so an older upstream revision can be measured without resetting
the working branch or rewriting files. No network is used at run time.

Initial commit: `1b858880dcac091b5e5f84f0e4d8617c35ba1392`.
Tested commit: `1b858880dcac091b5e5f84f0e4d8617c35ba1392`.

## Timing source and measurement

The four unmodified timing files come from pq-crystals/dilithium
`bba9534a3c5cbef66481cd6518d786e23ae601b5`, `ref/test/` (there is no root
`test/` directory at that revision). They match the Antrag bench copies byte
for byte. RDTSC is used; USE_RDPMC is not defined. The unchanged print_results
function receives iterations+1 timestamps for exactly iterations operations,
subtracts its own counter overhead, and computes the median. Thousand cycles
means RDTSC ticks divided by 1000. Loop/call overhead is included consistently.

System GCC: -O3 -march=native -std=gnu11. Ref additionally disables automatic
loop/SLP vectorization; algorithm SIMD intrinsics are selected only in the
upstream SIMD implementation. Exact flags are recorded per variant in
config.json, metadata.json and build logs. Messages have 32 bytes. Signing and
verification receive serialized byte keys and include all decoding/expansion
performed by the upstream byte API. KeyGen returns serialized keys.
Expanded-key Sign is reported only when a supported API is available.

QUICK=1: 11 timing operations, upstream KAT/self-tests, 100 generated signatures.
Default FULL: 10001 timing operations, upstream KAT/self-tests, 10000 generated
signatures. Only QUICK is executed in cloud. Full-scale runs are for the user's
local machine. No test assertions are disabled. The correctness and length
statistics reuse the same signature pool, using a fixed-seed key per build/set.
All signatures self-verify, cross-verify when another build exists, and are
checked for rejection after changing the message. Equality expectations are
configured explicitly; floating-point implementations can use cross verification
when byte equality is inappropriate. No result is declared complete unless all
required commands finish with zero status. The CSV contains medians and sizes;
raw timer output and correctness evidence are retained.

A bench-only xorshift64* byte stream (seed 1234567, fixed update and byte order in
driver.c) supplies reproducible test entropy where the API accepts an external
provider. This is for correctness vectors, not production randomness. For NIST
APIs the timing provider is the original randombytes implementation, renamed only
in its provider translation unit and routed through a bench wrapper; the algorithm
call sites remain unchanged. Callback APIs use the repository SHAKE generator
with fixed test seeds and OS-seeded timing state as documented below.

Missing system-library headers/libraries are compile/link checked at startup,
before algorithm builds. The runner never installs packages. Bash, Python 3.8+,
Git and system GCC are required; additional apt dependencies are listed below.

## Scheme-specific configuration and format

Cross-check implementation only; paper Falcon performance is from VecFalcon. This revision documents a 2026 best guess of future FIPS 206, not a published final standard. Compared with VecFalcon 61b326e: public keys are NTT encoded, encodings/hash-to-point are little-endian, signature infinity norm is capped at 840 instead of 2047, a 64-byte mu binds the hashed public key/context/message, secret keys include an additional 64-byte public-key hash, the base sampler uses 79 bits rather than 72, and SHAKE256x4 was removed. It is not a drop-in original round-3 Falcon implementation or interoperable wire format with the earlier VecFalcon API, despite the same public-key/signature lengths. Signatures remain padded 666/1280 bytes; exact unpadding parses the LSB-first compressed polynomial and checks against comp_decode. The scalar ref disables SIMD and uses software binary64, AVX2 uses native SIMD/FPU. Native degree-specific transcript KATs are mandatory for both. Public C API exposes only encoded keys; ExpandedSign is unavailable.

## Native-source compilation changes

No algorithm source patches. All source copies come from the tested commit.
Additional source selection, preprocessor options and include paths appear in
config.json. Configuration-only exceptions, if any, are documented below.

## Timing file checksums

* cpucycles.c: `31cc4c16b1e896b2cf7cc154aa21430329c0047cf9898a1865f9bfe9904f25e4`
* cpucycles.h: `7f1e2b68cf3e3c76076364af3c5350de61442450c477aec809da8de10e131838`
* speed_print.c: `533fc7bd12204078a5390cfb58c05d550b214850876609f8e98f7377b9d4f1b3`
* speed_print.h: `3946b0226c63125664eb443a20d43563e6d1ba7fa3be5c1b952cd29d1477b2ef`

Additional apt dependencies: none beyond build-essential, python3 and git.

No specific upstream revision was requested for c-fn-dsa; initial HEAD is used.
The initial commit is dated 2026-09-21. README's 2026-07-22 section explicitly
calls this the author's best guess of future FIPS 206, rather than an existing
published final standard. It must not be described as finalized FN-DSA.

Differences from VecFalcon's earlier c-fn-dsa-derived API are concrete:
- public keys hold NTT coefficients and encoding/hash-to-point is little-endian;
- a 64-byte mu is computed from hashed public key, context and message;
- encoded sk grows by 64 bytes, to 1345/2369, storing the public-key hash;
- the signature infinity bound is 840 instead of 2047;
- the base sampler uses 79 bits, and optional SHAKE256x4 is removed.
Both APIs emit padded 666/1280-byte signatures with pk sizes 897/1793, so size
agreement does not establish wire or algorithm equivalence to VecFalcon or
Falcon round 3. The paper comparison is a size reference only for this cross-check.

Ref uses FNDSA_AVX2=0,FNDSA_SSE2=0,FNDSA_NEON=0 and disabled compiler
vectorization, invoking the supported software binary64 path. AVX2 uses the
same sources with FNDSA_AVX2=1,FNDSA_SSE2=1 and AVX-512 disabled. The original
Makefile's clang/-O2 choice is not required for correctness; requested GCC/-O3
works and passes the original known answers. No FPU or algorithm code is patched.

The bench wrapper includes test_fndsa.c with its main renamed and invokes the
unchanged degree-specific inner_test_kat with its native expected-answer array.
Function/data sections plus --gc-sections omit unrelated native stress suites.
Both native signing KATs pass in both backends. Fixed-seed correctness vectors
are byte-identical across backends and verify in both directions. Timing uses
fndsa_keygen/fndsa_sign with system entropy; only correctness uses seeded APIs.
Length statistics parse the LSB-first unary coefficient stream after the
41-byte header/nonce prefix and independently validate lengths with comp_decode.
No expanded-key/stateful signing API is exposed by this C implementation.

Before any algorithm build, the runner also compile/links a standard C
header/runtime/libm probe. Failure reports apt package build-essential
(including libc6-dev). Exact extra per-build flags are printed near the
SUMMARY heading as well as retained in metadata and logs. This final
preflight/report change leaves the measured driver and QUICK values unchanged.
