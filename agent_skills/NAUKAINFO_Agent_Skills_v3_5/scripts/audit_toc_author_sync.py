#!/usr/bin/env python3
"""Ensure TOC author rows exactly match final AUTOR paragraphs in article order."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn

def norm(s): return re.sub(r'\s+',' ',(s or '')).strip()
def blocks(doc):
    for child in doc.element.body.iterchildren():
        if child.tag==qn('w:p'): yield 'p',Paragraph(child,doc)
        elif child.tag==qn('w:tbl'): yield 'tbl',Table(child,doc)

def collect_body(doc):
    bs=list(blocks(doc)); started=False; current=None; rec=[]
    for k,o in bs:
        if k!='p': continue
        sid=getattr(o.style,'style_id',''); t=norm(o.text)
        if sid=='SECTION': started=True; current=None
        elif started and sid=='AUTOR':
            if current is None: current={'authors':[],'title':None}
            current['authors'].append(t)
        elif started and sid=='11' and current:
            current['title']=t; rec.append(current); current=None
    return rec

def collect_toc(doc):
    bs=list(blocks(doc)); toc=False; table=None
    for k,o in bs:
        if k=='p' and norm(o.text).upper()=='TABLE OF CONTENTS': toc=True; continue
        if toc and k=='tbl': table=o; break
    rec=[]
    if not table: return rec
    rows=table.rows
    i=0
    while i<len(rows)-1:
        c=[norm(x.text) for x in rows[i].cells]
        n=[norm(x.text) for x in rows[i+1].cells]
        if len(c)>=3 and re.fullmatch(r'\d+\.',c[0]) and len(n)>=3 and n[1]:
            rec.append({'authors':[norm(x) for x in c[1].split(',') if norm(x)],'authors_text':c[1],'title':n[1]}); i+=2
        else: i+=1
    return rec

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('docx'); ap.add_argument('--out-json'); a=ap.parse_args()
    doc=Document(a.docx); body=collect_body(doc); toc=collect_toc(doc)
    mismatches=[]
    for idx,(b,t) in enumerate(zip(body,toc),1):
        if norm(', '.join(b['authors']))!=norm(t['authors_text']) or norm(b['title'])!=norm(t['title']): mismatches.append({'index':idx,'body':b,'toc':t})
    report={'file':a.docx,'body_articles':len(body),'toc_articles':len(toc),'mismatches':mismatches,'pass':len(body)==len(toc)==24 and not mismatches}
    payload=json.dumps(report,ensure_ascii=False,indent=2)
    if a.out_json: Path(a.out_json).write_text(payload,encoding='utf-8')
    print(payload); raise SystemExit(0 if report['pass'] else 2)
if __name__=='__main__': main()
