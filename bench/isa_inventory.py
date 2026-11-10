"""Static instruction counts; distinguish algorithm objects from postprocessing."""
import re,subprocess,json,os
from pathlib import Path

def count(path):
    cp=subprocess.run(['objdump','-d',str(path)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=dict(os.environ,LANG='C',LC_ALL='C'))
    if cp.returncode:raise RuntimeError(cp.stderr.decode())
    symbol='';rows=[];counts=dict(ymm=0,zmm=0,legacy_sse=0,vzeroupper=0,cpuid=0)
    for line in cp.stdout.decode(errors='replace').splitlines():
        m=re.match(r'^\s*[0-9a-f]+ <([^>]+)>:',line)
        if m:symbol=m[1]
        parts=line.split('\t')
        if len(parts)<3:continue
        ins=parts[-1].strip();mnemonic=ins.split(' ',1)[0]
        flags=dict(ymm=bool(re.search(r'%ymm\d',ins)),zmm=bool(re.search(r'%zmm\d',ins)),legacy_sse=bool(re.search(r'%xmm\d',ins)) and not mnemonic.startswith('v'),vzeroupper=mnemonic=='vzeroupper',cpuid=mnemonic=='cpuid')
        for k,v in flags.items():counts[k]+=int(v)
        if flags['legacy_sse'] or flags['cpuid']:rows.append(dict(symbol=symbol,instruction=ins))
    return dict(counts=counts,legacy_sse_and_cpuid_sites=rows)

def inventory(dest,output):
    dest=Path(dest);objects={}
    for p in sorted(dest.glob('*.o')):
        if p.stem.isdigit() or p.stem in ('driver','cpucycles','speed_print'):objects[p.name]=count(p)
    algorithm={k:sum(v['counts'][k] for name,v in objects.items() if name.split('.')[0].isdigit()) for k in ('ymm','zmm','legacy_sse','vzeroupper','cpuid')}
    data=dict(algorithm_objects=algorithm,whole_driver=count(dest/'driver'),objects=objects,note='Static counts are not executed instruction counts. Printer/timer code outside timed APIs is counted separately; shared libraries are excluded.')
    Path(output).write_text(json.dumps(data,indent=2)+'\n');return data
