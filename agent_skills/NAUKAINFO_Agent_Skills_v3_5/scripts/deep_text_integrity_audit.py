#!/usr/bin/env python3
"""Per-article deep lexical integrity audit for NAUKAINFO journals.

Usage:
  python deep_text_integrity_audit.py --journal final.docx --source-map source_map.json --out audit.json

source_map.json:
{
  "articles": [
    {"index": 1, "title": "...", "source_path": "...docx", "source_kind": "docx"},
    {"index": 2, "title": "...", "source_path": "...pdf", "source_kind": "pdf"}
  ]
}

The audit is fail-closed: unknown source-side deletions/replacements are reported as blocking.
PDF is fallback only; DOC/DOCX should be used whenever available.
"""
from pathlib import Path
from zipfile import ZipFile
from lxml import etree
import argparse, json, re, unicodedata, difflib, subprocess

WNS='http://schemas.openxmlformats.org/wordprocessingml/2006/main'; W='{%s}'%WNS; NS={'w':WNS}
APOST=str.maketrans({'’':"'",'‘':"'",'`':"'",'ʼ':"'",'′':"'",'´':"'"})
DASH=str.maketrans({'–':'-','—':'-','−':'-','‑':'-','‒':'-'})

def norm(s):
    return unicodedata.normalize('NFKC',s or '').translate(APOST).translate(DASH).replace('\u00ad','').replace('\ufeff','').casefold()

def tokens(s):
    raw=re.findall(r'https?://[^\s]+|www\.[^\s]+|[\w]+(?:[\'\-][\w]+)*',norm(s),flags=re.UNICODE)
    out=[]
    for t in raw:
        if t.startswith(('http://','https://','www.')): out.append(t.rstrip('.,;:)'))
        else: out.append(re.sub(r"[-']",'',t))
    return [x for x in out if x]

def visible_text(el):
    out=[]
    def walk(n):
        if etree.QName(n).localname=='AlternateContent':
            choices=[c for c in n if etree.QName(c).localname=='Choice']
            if choices: walk(choices[0]); return
        if n.tag==W+'t': out.append(n.text or ''); return
        if n.tag==W+'tab': out.append('\t'); return
        if n.tag in (W+'br',W+'cr'): out.append('\n'); return
        for c in n: walk(c)
        if n.tag in (W+'p',W+'tc'): out.append('\n')
    walk(el); return ''.join(out)

def docx_body(path):
    with ZipFile(path) as z: root=etree.fromstring(z.read('word/document.xml'))
    return root.find('.//w:body',NS)

def style(p):
    x=p.find('./w:pPr/w:pStyle',NS); return x.get(W+'val') if x is not None else ''

def pbb(p): return p.find('./w:pPr/w:pageBreakBefore',NS) is not None

def final_articles(path):
    children=list(docx_body(path)); raw=[i for i,x in enumerate(children) if x.tag==W+'p' and pbb(x)]
    starts=[]
    for j,i in enumerate(raw):
        e=raw[j+1] if j+1<len(raw) else len(children)
        if any(x.tag==W+'p' and style(x)=='11' for x in children[i:e]): starts.append(i)
    arts=[]
    for n,s in enumerate(starts):
        e=starts[n+1] if n+1<len(starts) else len(children)
        # The protected ETALON tail starts after a paragraph carrying sectPr.
        # Clip the last article at the first section break after its start.
        if n+1==len(starts):
            for k in range(s,e):
                x=children[k]
                if x.tag==W+'p' and x.find('./w:pPr/w:sectPr',NS) is not None:
                    e=k+1
                    break
        region=children[s:e]
        ti=next((k for k,x in enumerate(region) if x.tag==W+'p' and style(x)=='11'),None)
        if ti is None: continue
        title=' '.join(visible_text(region[ti]).split())
        text='\n'.join(visible_text(x) for x in region[ti+1:])
        arts.append({'index':n+1,'title':title,'tokens':tokens(text)})
    return arts

def source_text(path,kind):
    if kind in ('docx','dotx'):
        return '\n'.join(visible_text(x) for x in docx_body(path))
    if kind=='pdf':
        raw=subprocess.check_output(['pdftotext','-raw',str(path),'-'],text=True,errors='replace')
        raw=re.sub(r'(?<=[A-Za-zА-Яа-яІіЇїЄєҐґ])-\s*\n\s*(?=[A-Za-zА-Яа-яІіЇїЄєҐґ])','',raw)
        return raw
    raise ValueError(f'Unsupported source_kind: {kind}')

def after_title(text,title):
    src=tokens(text); tt=tokens(title)
    for i in range(max(0,len(src)-len(tt)+1)):
        if src[i:i+len(tt)]==tt: return src[i+len(tt):]
    L=len(tt); best=(0,-1.0)
    for i in range(max(1,len(src)-L+1)):
        r=difflib.SequenceMatcher(None,tt,src[i:i+L],autojunk=False).ratio()
        if r>best[1]: best=(i,r)
    return src[best[0]+L:]

MARKERS=set(tokens('анотація abstract keywords ключові слова список використаних джерел список використаної літератури література references reference bibliography literaturverzeichnis quellenverzeichnis liste der verwendeten quellen url doi'))
ROLES=set(tokens('аспірант студент здобувач викладач доцент професор кандидат доктор кафедра університет академія інститут коледж науковий керівник senior lecturer professor phd department university academy institute faculty city місто україна ukraine orcid email телефон'))

def allowed(chunk,pos):
    if not chunk: return True,'empty'
    if all(x.isdigit() for x in chunk): return True,'reference-numbering'
    if len(chunk)<=8 and set(chunk)<=MARKERS|{str(i) for i in range(1,1000)}: return True,'standardized-marker'
    if pos<100 and (set(chunk)&ROLES or any('@' in x for x in chunk)): return True,'frontmatter/contact'
    # URL joining/hyphen normalization is permitted only as a reference-entry normalization.
    if len(chunk)<=12 and any(x.startswith(('http://','https://','www.')) for x in chunk):
        return True,'reference-url-normalization'
    return False,'unapproved-body-change'

def allowed_insert(chunk):
    if not chunk: return True,'empty'
    if len(chunk)<=8 and set(chunk)<=MARKERS|{str(i) for i in range(1,1000)}:
        return True,'inserted-standard-marker'
    return False,'unapproved-final-insertion'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--journal',required=True); ap.add_argument('--source-map',required=True); ap.add_argument('--out',required=True)
    a=ap.parse_args(); mapping=json.loads(Path(a.source_map).read_text(encoding='utf-8'))['articles']
    finals={x['index']:x for x in final_articles(a.journal)}; rows=[]
    for m in mapping:
        f=finals.get(m['index']);
        if not f:
            rows.append({'index':m['index'],'title':m.get('title'),'status':'BLOCKED','reason':'final-article-not-found'}); continue
        src=after_title(source_text(Path(m['source_path']),m['source_kind']),f['title']); fin=f['tokens']
        sm=difflib.SequenceMatcher(None,src,fin,autojunk=False); matched=0; raw_ops=[]
        for tag,i1,i2,j1,j2 in sm.get_opcodes():
            if tag=='equal': matched+=i2-i1; continue
            raw_ops.append({'tag':tag,'source_range':[i1,i2],'final_range':[j1,j2],
                            'source_tokens':src[i1:i2],'final_tokens':fin[j1:j2],
                            'source_context_before':src[max(0,i1-12):i1],'source_context_after':src[i2:i2+12]})
        # PDF extraction can expose anchored/shape captions in a different lexical order.
        # Pair identical delete+insert chunks as REVIEW rather than declaring loss.
        review=[]; blocking=[]; allowed_ops=[]; paired=set()
        if m['source_kind']=='pdf':
            for di,d in enumerate(raw_ops):
                if d['tag']!='delete' or len(d['source_tokens'])<3: continue
                for ii,ins in enumerate(raw_ops):
                    if ii in paired or ins['tag']!='insert': continue
                    if d['source_tokens']==ins['final_tokens']:
                        d.update({'allowed':False,'reason':'legacy-object-order-review'})
                        ins.update({'allowed':False,'reason':'legacy-object-order-review'})
                        review.extend([d,ins]); paired.update({di,ii}); break
        for oi,rec in enumerate(raw_ops):
            if oi in paired: continue
            if rec['tag']=='insert':
                ok,reason=allowed_insert(rec['final_tokens']); rec.update({'allowed':ok,'reason':reason})
            else:
                ok,reason=allowed(rec['source_tokens'],rec['source_range'][0]); rec.update({'allowed':ok,'reason':reason})
            (allowed_ops if ok else blocking).append(rec)
        status='BLOCKED' if blocking else ('REVIEW' if review else 'PASS')
        rows.append({'index':m['index'],'title':f['title'],'source_path':m['source_path'],'source_kind':m['source_kind'],
                     'source_tokens':len(src),'final_tokens':len(fin),'matched_tokens':matched,'source_coverage':round(matched/max(1,len(src)),6),
                     'blocking_diffs':blocking,'review_diffs':review,'allowed_diffs':allowed_ops,'status':status})
    report={'journal':a.journal,'articles_compared':len(rows),
            'blocking_articles':sum(r['status']=='BLOCKED' for r in rows),
            'review_articles':sum(r['status']=='REVIEW' for r in rows),
            'confirmed_unapproved_changes':sum(len(r.get('blocking_diffs',[])) for r in rows),'articles':rows}
    report['status']='BLOCKED' if report['blocking_articles'] else ('REVIEW' if report['review_articles'] else 'PASS')
    Path(a.out).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':report['status'],'articles':len(rows),'blocking_articles':report['blocking_articles'],'review_articles':report['review_articles'],'out':a.out},ensure_ascii=False))
if __name__=='__main__': main()
