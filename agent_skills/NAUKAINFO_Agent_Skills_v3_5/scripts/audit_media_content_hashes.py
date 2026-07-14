#!/usr/bin/env python3
"""Audit DOCX media relationships and content hashes without modifying the file."""
from __future__ import annotations
import argparse, hashlib, json, posixpath, zipfile
from pathlib import Path
from lxml import etree

REL='http://schemas.openxmlformats.org/package/2006/relationships'
A='http://schemas.openxmlformats.org/drawingml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS={'rel':REL,'a':A,'r':R,'w':W}

def sha256(data: bytes) -> str: return hashlib.sha256(data).hexdigest()

def audit(path: Path) -> dict:
    with zipfile.ZipFile(path) as z:
        names=set(z.namelist())
        doc=etree.fromstring(z.read('word/document.xml'))
        rels=etree.fromstring(z.read('word/_rels/document.xml.rels'))
        relmap={r.get('Id'):r.get('Target') for r in rels}
        rids=doc.xpath('//a:blip/@r:embed',namespaces=NS)
        broken=[]; targets=[]
        for rid in rids:
            target=relmap.get(rid)
            if not target:
                broken.append({'rid':rid,'reason':'missing relationship'}); continue
            name=posixpath.normpath(posixpath.join('word',target))
            if name not in names:
                broken.append({'rid':rid,'target':target,'resolved':name,'reason':'missing part'}); continue
            targets.append({'rid':rid,'part':name,'sha256':sha256(z.read(name)),'bytes':len(z.read(name))})
        all_media=[{'part':n,'sha256':sha256(z.read(n)),'bytes':len(z.read(n))} for n in sorted(names) if n.startswith('word/media/')]
        drawing_paras=[]
        for p in doc.xpath('//w:body//w:p[.//w:drawing or .//w:pict or .//w:object]',namespaces=NS):
            st=(p.xpath('./w:pPr/w:pStyle/@w:val',namespaces=NS)or[''])[0]
            drawing_paras.append(st)
        return {'file':str(path),'embedded_blips':len(rids),'relationship_targets':targets,'all_media':all_media,'broken':broken,'drawing_paragraph_styles':drawing_paras,'pass':not broken}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('docx'); ap.add_argument('--out-json'); a=ap.parse_args()
    report=audit(Path(a.docx)); payload=json.dumps(report,ensure_ascii=False,indent=2)
    if a.out_json: Path(a.out_json).write_text(payload,encoding='utf-8')
    print(payload); raise SystemExit(0 if report['pass'] else 2)
if __name__=='__main__': main()
