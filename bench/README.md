# Offline benchmark

Requirements: Linux x86-64 with the required AVX2/FMA/BMI2 features, system GCC,
Git, Bash, Python 3.8+, and dependencies listed in NOTES.md. No sudo or network
is used by the runner. All subprocesses use LANG=C and LC_ALL=C.

```bash
QUICK=1 bash bench/run.sh   # smoke run only; cloud uses this command
bash bench/run.sh           # full local run
```

The runner builds the locally available tested commit recorded in config.json,
not whichever algorithm source happens to be checked out. Do not delete that
Git object or use an incomplete shallow clone. It builds all configured
parameters/backends, runs upstream tests, verifies the fixed-seed signature pool,
then measures byte-KeyGen/Sign/Verify and supported expanded-key Sign.

Results: bench/results/<UTC timestamp>/SUMMARY.md, bench.csv, metadata.json,
correctness.json, lengths.json, timings.json and logs. The ignored work/ tree
contains extracted source, binaries and test vectors. A failed run exits nonzero
and has no completed SUMMARY. QUICK and FULL are explicitly labeled in metadata
and the first SUMMARY heading. Compare FULL numbers only on the same local CPU.

See NOTES.md for format, length extraction, native RNG, revision selection,
compilation configuration and any paper-size discrepancy.

Current role/backend/protocol are recorded in NOTES.md and PROTOCOL.md. Main ref
is upstream hardware SSE2 with AVX2 disabled, not pure-C double. Software
binary64 is supplemental. Byte equality diagnostics precede mandatory cross-
verification for all backend pairs. STRICT_EQUAL=1 is an optional additional
stop after recording evidence; FP_CONTRACT=off enables a rounding ablation.

For the earlier failed FULL corpus, inspect without regenerating signatures:

```bash
python3 bench/audit_vectors.py /path/to/old/result --set FN-DSA-512
python3 bench/replay_case.py /path/to/old/result --set FN-DSA-512
```

The first command prints the first differing case and checks original cross-
verification; the second replays only that case with original and no-contract
compiler settings. The original vectors and metadata must still exist.
