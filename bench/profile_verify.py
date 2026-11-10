#!/usr/bin/env python3
"""Add Verify diagnostics to an existing result; no main timing is rerun."""
import json,os,sys
from pathlib import Path
import run as runner
from verify_diagnostics import run_profiles

def main():
    if len(sys.argv)!=2:raise RuntimeError('usage: python3 bench/profile_verify.py RESULT_DIRECTORY')
    out=Path(sys.argv[1]).resolve();meta=json.loads((out/'metadata.json').read_text())
    if '-ffp-contract=off' not in meta['flags']:raise RuntimeError('Use a result built with the current FP contraction rule')
    stage=out/'work/source'
    if not stage.exists():raise RuntimeError('Original work/source and object files are needed; otherwise rerun bench/run.sh')
    nt=11 if os.environ.get('QUICK')=='1' else 10001
    text=run_profiles(stage,out,meta['configuration'],meta['flags'],runner.CC,runner.call,nt,pk_ntt=runner.ROOT.name=='VecFalcon',profile_source=runner.BENCH/'verify_profile.c')
    (out/'verify-profile-provenance.json').write_text(json.dumps(dict(scale='QUICK' if nt==11 else 'FULL',iterations=nt,profile_commit=runner.call(['git','rev-parse','HEAD']).strip(),original_benchmark_commit=meta.get('benchmark_commit'),gcc=runner.call([runner.CC,'--version']).splitlines()[0],note='Original main timings and SUMMARY are not modified; instrumented diagnostics are separate.'),indent=2)+'\n')
    print(text);print('PASS:',out/'VERIFY_DIAGNOSTICS.md')
if __name__=='__main__':
    try:main()
    except Exception as exc:print('FAILED:',exc,file=sys.stderr);sys.exit(1)
