import csv,json,re,shutil
from pathlib import Path
from isa_inventory import inventory

def run_profiles(stage,out,cfg,base,cc,call,count,pk_ntt=False,profile_source=None):
    out=Path(out);stage=Path(stage);rows=[]
    if profile_source:shutil.copy2(profile_source,stage/'bench/verify_profile.c')
    for row in cfg['sets']:
        for variant in row['variants']:
            name=variant['name'];key=row['name']+'-'+name;dest=out/'work'/key
            inventory(dest,out/(key+'-isa.json'))
            if name not in ('ref','avx2'):continue
            folder=stage/variant['cwd'];flags=base+variant.get('flags',[])+['-I.','-I'+str(stage/'bench'),'-DBENCH_PK_NTT='+str(int(pk_ntt))]
            log=out/(key+'-verify-profile-build.log');obj=dest/'verify_profile.o'
            call([cc]+flags+['-include',stage/'bench'/'adapter.h','-c',stage/'bench'/'verify_profile.c','-o',obj],folder,log)
            objects=[dest/(str(i)+'.o') for i in range(len(variant['sources']))]+[dest/('extra'+str(i)+'.o') for i in range(len(variant.get('extra_sources',[])))]+[dest/'cpucycles.o',dest/'speed_print.o']
            symbols=['fndsa_mqpoly_decode','fndsa_mqpoly_ext_to_int']
            if pk_ntt:symbols+=['fndsa_mqpoly_int_to_ntt']
            if name=='avx2':
                symbols+=['fndsa_avx2_mqpoly_ext_to_int','fndsa_has_avx2']
                if pk_ntt:symbols+=['fndsa_avx2_mqpoly_int_to_ntt']
            exe=dest/'verify_profile'
            call([cc,obj]+objects+variant.get('libs',[])+['-Wl,--wrap='+s for s in symbols]+['-o',exe],folder,log)
            for clean in ([False,True] if name=='avx2' else [False]):
                args=[exe,count]+(['clean'] if clean else [])
                text=call(args,folder,out/(key+('-clean' if clean else '')+'-verify-profile.log'))
                meta=list(map(int,re.search(r'^PROFILE_META (.*)$',text,re.M)[1].split()))
                values={op:int(cycles) for op,cycles in re.findall(r'^(PKDecode|CoreVerify|VerifyInstrumented|DispatchDetect|SignInstrumented|SignDispatchDetect)\nmedian: (\d+) cycles/ticks',text,re.M)}
                if not all(x in values for x in ('PKDecode','CoreVerify','VerifyInstrumented')):raise RuntimeError('Missing Verify profile: '+key)
                sign_calls=re.search(r'^SIGN_DISPATCH_CALLS (\d+) (\d+) (\d+)$',text,re.M)
                rows.append(dict(sign_dispatch_calls=list(map(int,sign_calls.groups())) if sign_calls else None,set=row['name'],build=name,clean_before=clean,iterations=count,pk_includes_ntt=pk_ntt,hooks=meta,cycles=values))
    (out/'verify_breakdown.json').write_text(json.dumps(rows,indent=2)+'\n')
    with (out/'verify_breakdown.csv').open('w',newline='') as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(['parameter','build','clean_before','iterations','pk_decode_kcycles','core_verify_kcycles','instrumented_total_kcycles','dispatch_detect_kcycles'])
        for r in rows:w.writerow([r['set'],r['build'],r['clean_before'],r['iterations']]+[r['cycles'].get(op,0)/1000 for op in ('PKDecode','CoreVerify','VerifyInstrumented','DispatchDetect')])
    text='\nVerify diagnostic split (thousand TSC ticks; instrumented, separate from the main Verify metric):\n\n| Set | Build | vzeroupper before call | PK decode/preparation | Remaining core | Instrumented total | CPU dispatch (included in core) |\n|---|---|---|---:|---:|---:|---:|\n'
    for r in rows:text+='| %s | %s | %s | %.3f | %.3f | %.3f | %.3f |\n'%(r['set'],r['build'],r['clean_before'],*[r['cycles'].get(op,0)/1000 for op in ('PKDecode','CoreVerify','VerifyInstrumented','DispatchDetect')])
    text+='\nPK phase brackets original mqpoly_decode through initial representation conversion'+(' and PK NTT.' if pk_ntt else '; this version stores PK in NTT wire format, so no PK NTT is performed.')+' Core is the same-sample remainder, including PK/message hashing, dispatch, signature decoding and verification arithmetic. Linker hooks add boundary overhead; these diagnostic medians do not replace the main public API median, and medians need not add. The clean probe inserts only vzeroupper before the timed API. Static ISA counts are in *-isa.json.\n'
    text+='\nSign diagnostic (encoded-key API, fixed seed corpus; not a replacement for the main timing):\n\n| Set | Build | Instrumented Sign kcycles | CPU detection kcycles | Mean detection calls/sign | Max |\n|---|---|---:|---:|---:|---:|\n'
    for r in rows:
        if r['clean_before']:continue
        calls=r['sign_dispatch_calls'] or [0,0,1]
        text+='| %s | %s | %.3f | %.3f | %.4f | %d |\n'%(r['set'],r['build'],r['cycles'].get('SignInstrumented',0)/1000,r['cycles'].get('SignDispatchDetect',0)/1000,calls[0]/calls[2],calls[1])
    (out/'VERIFY_DIAGNOSTICS.md').write_text(text)
    return text
