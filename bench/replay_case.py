#!/usr/bin/env python3
"""Replay the first old ref/AVX2 mismatch and test compiler FP contraction.
Only three single-signature replays are generated; no timing or corpus search.
"""
import argparse, json, re, shutil, sys
from pathlib import Path
from audit_vectors import inspect_pair, read_vectors
import run as runner

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('result',type=Path);p.add_argument('--set',default='FN-DSA-512')
    a=p.parse_args()
    if not shutil.which('objdump'):raise RuntimeError('Missing objdump: apt install binutils')
    out=a.result.resolve();meta=json.loads((out/'metadata.json').read_text())
    cfg=meta['configuration'];row=next(x for x in cfg['sets'] if x['name']==a.set)
    n=1024 if a.set.endswith('1024') else 512
    pk=1+14*n//8;sk=65+(6 if n==512 else 5)*n//4+n
    original={v:out/'work'/(a.set+'-'+v+'.vectors') for v in ('ref','avx2')}
    evidence=out/'diagnostics'/(a.set+'-old-ref-avx2')
    report=inspect_pair(original['ref'],original['avx2'],pk,sk,32,dest=evidence)
    first=report['first_difference']
    if first is None:
        print('No differing signature found; key/count differences:',report['pk_equal'],report['sk_equal'],report['count_equal']);return 0
    evidence.mkdir(parents=True,exist_ok=True)
    (evidence/'first-difference.json').write_text(json.dumps(report,indent=2)+'\n')
    index=first['index_zero_based'];work=out/'work'/'single-case-replay';work.mkdir(parents=True,exist_ok=True)
    stage=work/'source'
    if stage.exists():raise RuntimeError('Replay workspace exists; preserve or move it before rerunning: '+str(stage))
    runner.archive(meta['tested_commit'],stage)
    binaries={};vectors={};log=evidence/'replay-build.log';base=meta['flags']
    buildinfo=[]
    for label,variant_name,off in [('old-ref','ref',False),('old-avx2','avx2',False),('avx2-no-contract','avx2',True)]:
        variant=next(v for v in row['variants'] if v['name']==variant_name)
        dest=work/label;dest.mkdir();folder=stage/variant['cwd']
        flags=base+variant.get('flags',[])+(['-ffp-contract=off'] if off else [])+['-I.','-I'+str(stage/'bench')]
        objects=[]
        for j,source in enumerate(variant['sources']):
            obj=dest/(str(j)+'.o');runner.call([runner.CC]+flags+['-c',source,'-o',obj],folder,log);objects.append(obj)
        for j,spec in enumerate(variant.get('extra_sources',[])):
            obj=dest/('extra'+str(j)+'.o');runner.call([runner.CC]+flags+spec.get('flags',[])+['-c',spec['path'],'-o',obj],folder,log);objects.append(obj)
        for name in ('cpucycles','speed_print'):
            obj=dest/(name+'.o');runner.call([runner.CC]+base+['-c',stage/'bench'/(name+'.c'),'-o',obj],folder,log);objects.append(obj)
        driver=dest/'driver.o';runner.call([runner.CC]+flags+['-include',stage/'bench'/'adapter.h','-c',stage/'bench'/'driver.c','-o',driver],folder,log)
        exe=dest/'driver';runner.call([runner.CC,driver]+objects+variant.get('libs',[])+['-o',exe],folder,log)
        vec=dest/'case.vectors';runner.call([exe,'generate',1,vec,index],log=evidence/'replay.log')
        binaries[label]=exe;vectors[label]=vec
        asm=runner.call(['objdump','-d',exe],log=None)
        fma=[s for s in asm.splitlines() if re.search(r'\bv(?:f|fn)m(?:add|sub)',s)]
        (evidence/(label+'-fma.txt')).write_text('\n'.join(fma)+'\n')
        buildinfo.append(dict(label=label,flags=flags,fma_instructions=len(fma)))
    sigs={k:read_vectors(v,pk,sk)[1][0][1] for k,v in vectors.items()}
    old_sigs={k:read_vectors(v,pk,sk)[1][index][1] for k,v in original.items()}
    findings=dict(old_ref_reproduced=sigs['old-ref']==old_sigs['ref'],old_avx2_reproduced=sigs['old-avx2']==old_sigs['avx2'],avx2_no_contract_equals_old_ref=sigs['avx2-no-contract']==old_sigs['ref'])
    cross=[]
    for verifier,exe in binaries.items():
        for signer,vec in vectors.items():
            runner.call([exe,'check',1,vec,index],log=evidence/'replay.log');cross.append(dict(verifier=verifier,signer=signer,status='PASS'))
    result=dict(first_sample_one_based=index+1,seeds={k:v for k,v in first.items() if 'seed_hex' in k or k=='message_hex'},builds=buildinfo,findings=findings,cross_verification=cross,gcc=runner.call([runner.CC,'--version']).splitlines()[0])
    result['interpretation']='FP contraction accounts for this first differing signature in this replay environment.' if all(findings.values()) else 'Cause unresolved: inspect replay findings; no implementation change was made.'
    (evidence/'replay-report.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as exc:print('FAILED:',exc,file=sys.stderr);raise SystemExit(1)
