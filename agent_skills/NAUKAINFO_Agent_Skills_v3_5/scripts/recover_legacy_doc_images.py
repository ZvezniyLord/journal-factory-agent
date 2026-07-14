#!/usr/bin/env python3
"""Recover embedded raster images from legacy binary .doc OLE streams.

This is a forensic fallback. It never edits the source .doc. Recovered files are
written to a separate directory and must be visually matched to the source page.
"""
from __future__ import annotations
import argparse, hashlib, json, struct
from pathlib import Path
import olefile

SIGS=[('png',b'\x89PNG\r\n\x1a\n'),('jpg',b'\xff\xd8\xff')]

def carve_stream(name: str, data: bytes, out: Path):
    found=[]
    for ext,sig in SIGS:
        start=0
        while True:
            i=data.find(sig,start)
            if i<0: break
            if ext=='png':
                end=data.find(b'IEND',i)
                if end<0: start=i+1; continue
                end+=8
            else:
                end=data.find(b'\xff\xd9',i+3)
                if end<0: start=i+1; continue
                end+=2
            blob=data[i:end]
            digest=hashlib.sha256(blob).hexdigest()
            path=out/f'{name.replace("/","_")}_{ext}_{i}_{digest[:10]}.{ext}'
            path.write_bytes(blob)
            found.append({'stream':name,'offset':i,'path':str(path),'bytes':len(blob),'sha256':digest})
            start=end
    return found

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('doc'); ap.add_argument('out_dir'); ap.add_argument('--out-json'); a=ap.parse_args()
    src=Path(a.doc); out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    if not olefile.isOleFile(src): raise SystemExit('not an OLE compound document')
    results=[]
    with olefile.OleFileIO(src) as ole:
        for parts in ole.listdir(streams=True,storages=False):
            name='/'.join(parts); data=ole.openstream(parts).read(); results.extend(carve_stream(name,data,out))
    report={'source':str(src),'out_dir':str(out),'recovered':results,'count':len(results)}
    payload=json.dumps(report,ensure_ascii=False,indent=2)
    if a.out_json: Path(a.out_json).write_text(payload,encoding='utf-8')
    print(payload)
if __name__=='__main__': main()
