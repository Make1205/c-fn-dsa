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


## Current protocol and floating-point backend (2026-11-10)

This section supersedes the old ref/vectorization/timing descriptions above.
All modifications are inside bench/; no algorithm file, table, sampler, encoding
or RNG call site has been modified. Tested revisions remain pinned. See
[PROTOCOL.md](PROTOCOL.md) for the common byte-key rule from the LITHIUM audit;
its separate local 3% numerical calibration is not claimed to have passed.

System GCC uses -O3 -march=native -std=c99 -D_DEFAULT_SOURCE plus the recorded
backend macros/options. _DEFAULT_SOURCE is required to declare getentropy and
O_CLOEXEC used by the upstream Linux sysrng.c under strict C99; GNU C previously
enabled these declarations implicitly. No extra -fno-tree-vectorize or
-fno-tree-slp-vectorize is applied to the new builds. The source Makefiles use
Clang/O2 or their artifact defaults, but those defaults are not required by the
API; GCC/O3 follows the requested common protocol.

Each timing round generates fresh byte-form keys, signs a 32-byte zero message
from the byte sk (including decode and expansion), and verifies from the byte pk
(including decode and hashing). Twenty complete warmup triples are discarded.
Timing uses the upstream OS RNG, with no preexpanded key or cached matrix
supplied by bench. The four Dilithium bba9534 timing files are unchanged;
RDTSC intervals are passed to unchanged print_results for overhead subtraction
and odd-sample medians in thousand ticks. No claim of equivalence with COPA's
59-byte/RDTSCP/instrumented source workload is made.

Main ref: FNDSA_AVX2=0, FNDSA_SSE2=1, FNDSA_NEON=0; -msse2 -mno-avx
-mno-avx2 -mno-avx512f -mno-fma. It uses upstream hardware IEEE binary64 through
SSE2 intrinsics, including packed operations in FFT. It is a non-AVX2 x86
fallback, **not a pure-C portable double implementation**. The pinned sources
have no FALCON_FPNATIVE selector: disabling SSE2 selects uint64_t fpr software
emulation, not hardware double. The other native hardware paths use NEON or
RISC-V inline assembly. Providing a pure-C hardware-double backend would require
implementation changes, which are prohibited. The chosen existing SSE2 fallback
is reported explicitly in metadata and SUMMARY rather than described as scalar
portable C. This limitation awaits the user's backend preference if strict
no-intrinsics portability remains mandatory.

The original software configuration remains as soft, only in a supplemental
SUMMARY table. The avx2 backend's source and selector options are retained;
all builds adopt the fresh-triple timing protocol. Supplemental soft also
participates in all six ordered cross-verification pairs per degree. Keygen is
integer fixed-point; hardware-versus-emulated binary64 primarily concerns Sign.
Neither package requires GMP or an external floating-point library.

For comparison: Antrag ref uses native double/libm with its algorithm AVX2/FMA
selectors disabled; HAWK ref keygen and signing are integer/fixed-point and use
neither floating point nor GMP. Those repositories are read-only in this task.
The three ref labels therefore describe different actual arithmetic backends.

QUICK=1 uses 11 timing samples and 100 signatures per backend/degree, plus the
unchanged configured native KAT/self-tests. FULL uses 10001 and 10000 locally.
Actual encoded lengths still use the existing signature-bit parser checked
against native comp_decode, never heuristic removal of trailing zero bytes.
All per-backend means/maxima and first byte differences appear in SUMMARY.

Byte equality is recorded for every backend pair, but cross-verification is
the default acceptance criterion. Native KAT fixture values/assertions remain
strict. STRICT_EQUAL=1 optionally also fails on a byte difference **after** all
cross-verification checks and diagnostic records have been saved. All normal
runs keep byte-difference evidence, not merely a pass/fail equality boolean.

When a signature differs, diagnostics/<set>-<pair>/equality.json contains its
first zero-based index and one-based sample, signing/keygen seed, message,
complete signatures, hashes and byte offset; left/right.vectors retain a single
replayable case with the encoded keys. No differing sample has been observed
in the current c-fn-dsa QUICK corpus. This does not resolve an earlier FULL
failure on a different machine/corpus size.


## Historical reproducibility audit (local FULL case now resolved below)

c-fn-dsa is now the primary Falcon-family measurement. Tested code is
1b858880dcac091b5e5f84f0e4d8617c35ba1392 (README's pre-standard FIPS 206 guess,
not finalized FN-DSA or Falcon round-3). pk and padded signature sizes remain
897/666 and 1793/1280 at q=12289; secret keys include a 64-byte public-key hash.
These matching paper sizes do not imply interoperability with VecFalcon's older
version: encoding/NTT public key, mu construction and sampler rules changed.
The API exposes only encoded keys; there is no expanded-key Sign operation.

Pinned README.md:82-84 says, concerning the Rust implementation:
"It is interoperable (indeed, it reproduces the same test vectors)".
README.md:67-69 says SHAKE256x4 was removed while "breaking test vector
reproducibility". These support checking the provided shared KATs. They are
not an explicit universal promise that every arbitrary seed yields identical
signatures under every C compiler's backend/optimization settings. The searched
README, Makefile, fndsa.h and test framework contain no such universal promise.
Nevertheless sign_inner.h:16 requires exact IEEE binary64 roundTiesToEven,
and its RISC-V note at 344-351 explicitly warns about compiler contraction.
Thus we keep all native KATs and record every mismatch; we do not dismiss the
reported discrepancy as an established harmless floating-point difference or
assert that upstream never intends reproducibility. Default cross-verification
is based on the documented public interoperability/KAT guarantees, without the
old bench's unsupported universal equality assertion.

Evidence in diagnosis/legacy-fma.json and legacy-avx2-fma.txt shows actual
FMA instructions in the previous cloud GCC14 AVX2 binary built with
-O3 -march=native. Fused multiply/add can round differently from a separate
binary64 multiply and add. This is an observed build property and a plausible
mechanism, **not proof that it caused the user's GCC11 FULL mismatch**.
No implementation bug is diagnosed or patched without a reproducing sample.
There is also a distinct final-arithmetic path in sign_core.c:192ff: software
binary64 performs inverse FFT then modular integer basis arithmetic, while the
hardware path applies the basis in FFT space before inverse FFT and rounding.
Floating operation ordering therefore need not be identical merely because
both backends use binary64. This too is a source-level difference, not an
established explanation for the missing local failure case.
Optional FP_CONTRACT=off applies -ffp-contract=off for a rounding ablation and
is recorded in build metadata; it is not silently applied to historical results.

The user's original failed FULL vectors are not present in this cloud checkout;
only the earlier 100-sample QUICK vectors are available. Consequently the first
FULL mismatching sample, and whether all of its 10000 signatures cross-verify,
were unknown at that stage; the user has since supplied the resolution recorded below. The old runner raised on equality before running cross-verify,
so an old equality error alone supplies no verification verdict. The new runner
saves diagnostics and cross-verifies before any optional strict equality stop.
Cloud performed QUICK only, no 10000-sample search.

### Inspect existing failed results locally (no signature generation)

After updating bench, set RESULT to the **old failed FULL** result directory:

```bash
RESULT="$PWD/bench/results/<old-failed-full-timestamp>"
LANG=C LC_ALL=C python3 bench/audit_vectors.py "$RESULT" --set FN-DSA-512
```

This parses the old ref/avx2 vectors, finds the first differing signature,
derives its exact fixed seed/message, saves both signatures and verifies all
existing signatures using the original binaries. It does not rerun keygen or
signing. It prints NOT_RUN if original binaries are missing; missing vectors
cannot be reconstructed from an equality exception alone. Its JSON includes
both vector hashes, counts, key equality and verifier exit/output evidence.
Report: diagnostics/FN-DSA-512-ref-avx2/report.json within that result directory.

For that first case only, test the FMA hypothesis on the original local toolchain:

```bash
LANG=C LC_ALL=C python3 bench/replay_case.py "$RESULT" --set FN-DSA-512
```

This extracts the old tested commit locally, reads its recorded original flags,
and builds three replay binaries: original software ref, original AVX2, AVX2
with only -ffp-contract=off added. It generates exactly one signature per build
at the first mismatching index (skip deterministic seed bytes, not preceding
signatures), checks reproduction against the original signatures, and cross-
verifies the single case in all combinations. No source is patched. The report
only attributes this case to FP contraction when both originals reproduce and
the no-contract AVX2 result equals the old ref signature. Otherwise cause stays
unresolved. Requires binutils/objdump in addition to normal dependencies. It does
not search or time a FULL corpus. Preserve work/single-case-replay before retrying.
Report: diagnostics/FN-DSA-512-old-ref-avx2/replay-report.json.

The final QUICK ref-backend-proof.json inspects algorithm and driver object
files: SSE hardware FP is present and no YMM/ZMM/FMA instruction occurs there.
The unchanged speed_print object uses base -march=native and may be compiler
auto-vectorized, including AVX instructions on the cloud CPU; this is post-
measurement statistics outside the timed algorithm call, not selection of an
AVX2 algorithm backend. No extra auto-vectorization suppression is used.


## Resolved local FULL failure: FP contraction (user report, 2026-11-10)

The user completed the original local investigation. First mismatch: sample
3462, zero-based index 3461. The signatures differ starting at byte 41, using
the byte-position convention in the user's report. Both signatures passed
cross-verification. Original AVX2 contained 15 compiler-generated FMA
instructions; adding only -ffp-contract=off reduced this count to zero and
made that signature byte-identical to ref. replay_case.py reported
avx2_no_contract_equals_old_ref=true. The cause is floating-point contraction,
not an implementation defect. This is user-supplied local evidence; the original
full vectors/replay JSON were not uploaded, and no raw hashes/seeds are invented.
The report establishes this case; it is not a claim that all 10000 signatures
of that historical run were independently checked in cloud.

All three current variants (hardware ref, AVX2, supplemental software) now use
-ffp-contract=off. An object/executable audit requires zero FMA. Ref/AVX2 byte
equality is restored as a mandatory acceptance condition, in addition to all
ordered cross-verifications; soft equality stays diagnostic unless STRICT_EQUAL=1.
The old permissive-default description above is historical and superseded.
Every QUICK/FULL run also replays index 3461 directly (skip seed bytes, not 3461
signatures) and requires ref/AVX2 equality plus both cross-verifications. The
100/10000 ordinary correctness and length samples remain separate from this
single targeted regression. No algorithm implementation has been changed.

For this paper's measurement c-fn-dsa is primary; VecFalcon is backup. Version
and encoding differences from the older VecFalcon remain documented above.


## 2026-11-10: native ref ISA and Falcon performance diagnosis

Main public-API timing is unchanged. `verify_profile.c` is a separate bench-only
linker-hook diagnostic; it never patches algorithm sources, caches CPU detection,
or bypasses the public API. `profile_verify.py RESULT_DIRECTORY` reuses that
result's original algorithm objects and adds VERIFY_DIAGNOSTICS.md, a CSV/JSON
breakdown and static ISA inventory. Existing successful FULL main numbers remain
valid; profiling them does not require rerunning the main benchmark. Keep the
result's work/source directory. Use the same GCC version as the original build.

Ref explicitly selects hardware floating point/SSE2 and disables AVX ISA generation
(-mno-avx -mno-avx2 -mno-avx512f -mno-fma). Counting algorithm objects, not just
the executable, finds ZERO YMM instructions in ref. The executable has eight
YMM instructions in unmodified speed_print.o (statistics after timing), which
are not an AVX2 algorithm backend. See *-isa.json for separate counts and sites.

Both variants start Verify with serialized public keys and perform the same
logical decoding, hashing and verification. AVX2 does not pre-expand extra key
material. Its public entry calls fndsa_has_avx2() without caching. util.c uses
__get_cpuid_count(7,0), which emits two serializing CPUID instructions (maximum
leaf query then leaf 7), plus XGETBV. The scalar build compiles this dispatch
away. This is original library behavior, retained inside the main timing.

The AVX2 algorithm objects have zero legacy SSE instructions and include
vzeroupper at returns; the scalar objects use legacy SSE and no AVX. Therefore
there is no evidence for an internal legacy-SSE/AVX transition as the principal
Verify penalty. Static counts exclude shared libraries and are not dynamic
execution counts. A second diagnostic inserts vzeroupper BEFORE the timed call;
it did not consistently reduce the QUICK measurements. These observations do
not prove all platform/library transition overhead is absent.

PK timing continuously brackets original mqpoly_decode and the initial key
representation preparation. Remaining core includes dispatch, public-key/message
hashing, signature decoding and verification arithmetic. Hooks add timing and
call overhead. Per-sample total minus PK yields core, then each median is taken;
medians need not add. These are diagnostics, not replacement publication numbers.
The Sign diagnostic also reports CPU-detection calls per fresh-key signature.

Cloud tests use QUICK=1 only. CPUID is particularly expensive on this cloud CPU:
about 23-24 thousand ticks per c-fn-dsa AVX2 Verify. This constant offset is
consistent with the user's 25.4k/23.1k gaps for n=512/1024, but is NOT a measurement
of the user's CPU. Run the diagnostic locally before assigning its exact share.
No universal AVX2 speedup or SSE-transition explanation is inferred from QUICK.

Local command (after fetching bench; select an existing successful FULL result):

```bash
python3 bench/profile_verify.py bench/results/<FULL-directory>
```

A new `bash bench/run.sh` also includes these diagnostics automatically. Ref/AVX2
byte equality and cross-verification remain mandatory. All variants retain
-ffp-contract=off and the zero-FMA audit. c-fn-dsa is the paper's primary Falcon
measurement; VecFalcon is the alternative implementation.

This version stores the public key in NTT wire form; both backends decode it and
convert external to internal coefficients, with NO public-key NTT. Cloud QUICK
n=512 ref/AVX2 PK = 1.325/1.143k, remaining core = 34.319/52.779k,
AVX2 dispatch = 23.087k; n=1024 PK = 2.391/2.313k, core = 65.571/84.317k,
dispatch = 23.997k (20261110T131034.028237Z). Ref algorithm YMM=0;
AVX2 algorithm YMM=8976, legacy SSE=0, vzeroupper=203.
The current Sign FP kernel is the SSE2 hardware path in both builds; this source
version performs no AVX2 CPU dispatch during Sign. QUICK confirmed zero detection
calls. Similar Sign timings therefore do not indicate a wrongly selected ref.
