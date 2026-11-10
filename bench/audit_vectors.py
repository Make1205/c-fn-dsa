#!/usr/bin/env python3
"""Inspect existing vectors without generating signatures or changing sources."""
import argparse, hashlib, json, struct, subprocess
from pathlib import Path

MASK=(1<<64)-1

def seeds(index, key_bytes):
    state=(1234567+0x9e3779b97f4a7c15)&MASK
    def fill(n):
        nonlocal state
        out=bytearray()
        for _ in range(n):
            state ^= state>>12
            state ^= (state<<25)&MASK
            state ^= state>>27
            out.append(((state*2685821657736338717)&MASK)>>56)
        return bytes(out)
    key=fill(key_bytes)
    for _ in range(index): fill(40)
    return dict(keygen_seed_hex=key.hex(),signing_seed_hex=fill(40).hex(),
                message_hex=bytes((index+j)&255 for j in range(32)).hex())

def read_vectors(path, pk_bytes, sk_bytes):
    data=Path(path).read_bytes()
    start=pk_bytes+sk_bytes
    if len(data)<start: raise ValueError('truncated key header: '+str(path))
    records=[];pos=start
    while pos<len(data):
        if len(data)-pos<8: raise ValueError('truncated length')
        n=struct.unpack_from('<Q',data,pos)[0]
        if n==0 or n>10000 or n>len(data)-pos-8: raise ValueError('invalid signature length')
        records.append((pos,data[pos+8:pos+8+n]));pos+=8+n
    return data,records

def inspect_pair(left,right,pk_bytes,sk_bytes,key_seed_bytes,dest=None):
    a,ar=read_vectors(left,pk_bytes,sk_bytes);b,br=read_vectors(right,pk_bytes,sk_bytes)
    diffs=[i for i in range(min(len(ar),len(br))) if ar[i][1]!=br[i][1]]
    r=dict(left=str(left),right=str(right),left_sha256=hashlib.sha256(a).hexdigest(),
           right_sha256=hashlib.sha256(b).hexdigest(),left_count=len(ar),right_count=len(br),
           pk_equal=a[:pk_bytes]==b[:pk_bytes],sk_equal=a[pk_bytes:pk_bytes+sk_bytes]==b[pk_bytes:pk_bytes+sk_bytes],
           byte_equal=a==b,differing_signatures=len(diffs),count_equal=len(ar)==len(br),first_difference=None)
    r['first_file_byte_offset']=next((i for i,(x,y) in enumerate(zip(a,b)) if x!=y),min(len(a),len(b)) if a!=b else None)
    if diffs:
        i=diffs[0];x=ar[i][1];y=br[i][1]
        j=next((j for j in range(min(len(x),len(y))) if x[j]!=y[j]),min(len(x),len(y)))
        r['first_difference']=dict(index_zero_based=i,sample_one_based=i+1,signature_byte_offset=j,
            left_length=len(x),right_length=len(y),left_signature_sha256=hashlib.sha256(x).hexdigest(),
            right_signature_sha256=hashlib.sha256(y).hexdigest(),
            left_signature_hex=x.hex(),right_signature_hex=y.hex(),**seeds(i,key_seed_bytes))
        if dest:
            dest=Path(dest);dest.mkdir(parents=True,exist_ok=True)
            for label,data,records in [('left',a,ar),('right',b,br)]:
                sig=records[i][1]
                (dest/(label+'.vectors')).write_bytes(data[:pk_bytes+sk_bytes]+struct.pack('<Q',len(sig))+sig)
    return r

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('result',type=Path)
    p.add_argument('--scheme',choices=['c-fn-dsa','VecFalcon'],default='c-fn-dsa')
    p.add_argument('--set',default='FN-DSA-512')
    p.add_argument('--left',default='ref');p.add_argument('--right',default='avx2')
    args=p.parse_args();n=1024 if args.set.endswith('1024') else 512
    pk=1+14*n//8;sk=1+(6 if n==512 else 5)*n//4+n+(64 if args.scheme=='c-fn-dsa' else 0)
    work=args.result/'work';target=args.result/'diagnostics'/(args.set+'-'+args.left+'-'+args.right)
    names=[args.set+'-'+v for v in (args.left,args.right)]
    paths=[work/(name+'.vectors') for name in names]
    report=inspect_pair(*paths,pk,sk,32 if args.scheme=='c-fn-dsa' else 40,dest=target)
    meta_path=args.result/'metadata.json'
    if meta_path.exists():
        meta=json.loads(meta_path.read_text());report['source_run']={k:meta.get(k) for k in ('scale','signatures','gcc','cpu','tested_commit','benchmark_commit')}
    report['cross_verification']=[]
    for name,other,count in [(names[0],paths[1],report['right_count']),(names[1],paths[0],report['left_count'])]:
        exe=work/name/'driver'
        if not exe.exists():
            report['cross_verification'].append(dict(verifier=name,status='NOT_RUN_BINARY_MISSING'));continue
        cmd=[str(exe.resolve()),'check',str(count),str(other.resolve())]
        try:
            cp=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env=dict(__import__('os').environ,LANG='C',LC_ALL='C'))
            report['cross_verification'].append(dict(verifier=name,status='PASS' if cp.returncode==0 else 'FAIL',returncode=cp.returncode,output=cp.stdout.decode(errors='replace')))
        except OSError as exc:
            report['cross_verification'].append(dict(verifier=name,status='NOT_RUN_BINARY_ERROR',error=str(exc)))
    target.mkdir(parents=True,exist_ok=True)
    output=target/'report.json';output.write_text(json.dumps(report,indent=2)+'\n')
    print('Report:',output)
    short={k:v for k,v in report.items() if k!='first_difference'}
    short['first_difference']=({k:v for k,v in report['first_difference'].items() if not k.endswith('signature_hex')} if report['first_difference'] else None)
    print(json.dumps(short,indent=2))
    return 1 if any(x['status']!='PASS' for x in report['cross_verification']) else 0

if __name__=='__main__':
    raise SystemExit(main())
