from __future__ import annotations
import copy, json, re, shutil, tempfile, zipfile, subprocess
from pathlib import Path
from lxml import etree

SRC=Path('/mnt/data/JOURNAL_136_FULL_RELEASE_v31.docx')
OUT_STAGE=Path('/mnt/data/JOURNAL_136_FULL_RELEASE_v32_STAGE.docx')
OUT_FINAL=Path('/mnt/data/JOURNAL_136_FULL_RELEASE_v32_FINAL.docx')
REPORT=Path('/mnt/data/JOURNAL_136_FULL_RELEASE_v32_QA.json')
TOD_SRC=Path('/mnt/data/136_safe/018_2a4209b9.docx')
RENDER='/home/oai/skills/docx/render_docx.py'
RENDER_STAGE=Path('/mnt/data/render_v32_stage')
RENDER_FINAL=Path('/mnt/data/render_v32_final')

W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
WP='http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'
NS={'w':W,'r':R,'wp':WP,'a':'http://schemas.openxmlformats.org/drawingml/2006/main','v':'urn:schemas-microsoft-com:vml'}
q=lambda x:f'{{{W}}}{x}'
XMLSPACE='{http://www.w3.org/XML/1998/namespace}space'

LISTENERS=[
    ('Pivkach Iryna',None),
    ('Lydia Danylenko',None),
    ('Vasyl Kalchugin',None),
    ('Mariia Nazarenko',None),
    ('Valentyna Goshovska',None),
    ('Olena Zorczykowska','REPORT: APPLICATION OF FAIRY TALE THERAPY FOR THE ADAPTATION OF CHILDREN IN A MULTICULTURAL ENVIRONMENT'),
]

def p_text(el): return re.sub(r'\s+',' ',''.join(el.xpath('.//w:t/text()',namespaces=NS))).strip()
def style(p):
    x=p.find('w:pPr/w:pStyle',NS); return x.get(q('val')) if x is not None else ''
def ppr(p):
    x=p.find(q('pPr'))
    if x is None: x=etree.Element(q('pPr')); p.insert(0,x)
    return x

def set_page_break_before(p,on=True):
    pp=ppr(p); x=pp.find(q('pageBreakBefore'))
    if on and x is None: etree.SubElement(pp,q('pageBreakBefore'))
    if not on and x is not None: pp.remove(x)

def is_blank(p): return p.tag==q('p') and not p_text(p) and not p.xpath('.//w:drawing|.//w:pict|.//w:object',namespaces=NS)
def is_standalone_pagebreak(p): return p.tag==q('p') and not p_text(p) and bool(p.xpath('.//w:br[@w:type="page"]',namespaces=NS))

def replace_text_in_paragraph(p,text):
    for ch in list(p):
        if ch.tag!=q('pPr'): p.remove(ch)
    r=etree.SubElement(p,q('r')); t=etree.SubElement(r,q('t'))
    if text.startswith(' ') or text.endswith(' '): t.set(XMLSPACE,'preserve')
    t.text=text

def set_cell_text(tc,text,style_id):
    ps=tc.findall('w:p',NS)
    if not ps:
        p=etree.SubElement(tc,q('p')); ps=[p]
    p=ps[0]
    for extra in ps[1:]: tc.remove(extra)
    pp=ppr(p); st=pp.find(q('pStyle'))
    if st is None: st=etree.SubElement(pp,q('pStyle'))
    st.set(q('val'),style_id)
    replace_text_in_paragraph(p,text)

def strip_leading_spaces_preserve_runs(p):
    removed=0
    for t in p.xpath('.//w:t',namespaces=NS):
        s=t.text or ''
        if not s: continue
        m=re.match(r'^[ \t\u00a0]+',s)
        if m:
            removed+=len(m.group(0)); t.text=s[len(m.group(0)):]
            if not t.text: t.text=''
        break
    return removed

def find_tail_start(body):
    for i,ch in enumerate(body):
        if ch.tag==q('p') and p_text(ch)=='SCIENCE IN THE MODERN WORLD' and i>1000:return i
    raise RuntimeError('tail start not found')

def article_starts(body,tail):
    out=[]
    for i,ch in enumerate(body[:tail]):
        if ch.tag==q('p') and style(ch)=='UDC':
            j=i-1
            while j>=0 and is_blank(body[j]): j-=1
            out.append(j if j>=0 and body[j].tag==q('p') and style(body[j])=='SECTION' else i)
    # dedupe
    seen=[]
    for x in out:
        if x not in seen: seen.append(x)
    return seen

def remove_standalone_breaks(body,start,tail):
    n=0
    for ch in list(body[start:tail]):
        if is_standalone_pagebreak(ch): body.remove(ch); n+=1
    return n

def add_pagebreak_before_articles(body,starts):
    for s in starts: set_page_break_before(body[s],True)

def remove_blank_before_article_starts(body,tail):
    starts=article_starts(body,tail); n=0
    for s in reversed(starts):
        while s>0 and is_blank(body[s-1]): body.remove(body[s-1]); s-=1; n+=1
    return n

def restore_todorova_figure2(work,root,body):
    # Source second drawing paragraph (after first figure caption); use already packaged image32.png/rId99.
    with zipfile.ZipFile(TOD_SRC) as z:
        srcroot=etree.fromstring(z.read('word/document.xml')); srcbody=srcroot.find('w:body',NS)
        draw_ps=[p for p in srcbody.findall('w:p',NS) if p.xpath('.//w:drawing|.//w:pict',namespaces=NS)]
        if len(draw_ps)<2: raise RuntimeError('Todorova source second figure not found')
        newp=copy.deepcopy(draw_ps[1])
    for el in newp.xpath('.//*[@r:embed]',namespaces=NS): el.set(f'{{{R}}}embed','rId99')
    # unique docPr ids
    maxid=0
    for x in root.xpath('//wp:docPr',namespaces=NS):
        try:maxid=max(maxid,int(x.get('id','0')))
        except:pass
    for x in newp.xpath('.//wp:docPr',namespaces=NS): maxid+=1; x.set('id',str(maxid))
    # Canonical figure object style.
    pp=ppr(newp); st=pp.find(q('pStyle'))
    if st is None: st=etree.SubElement(pp,q('pStyle'))
    st.set(q('val'),'ad')
    jc=pp.find(q('jc'))
    if jc is None: jc=etree.SubElement(pp,q('jc'))
    jc.set(q('val'),'center')
    # find caption 2 in final and insert directly before it if missing drawing there
    cap=None
    for i,ch in enumerate(body):
        if ch.tag==q('p') and re.match(r'^Рис\.\s*2\.',p_text(ch),re.I): cap=i
    if cap is None: raise RuntimeError('Todorova figure 2 caption not found')
    # ensure caption is in Todorova region and previous node has no drawing
    if cap<1300: raise RuntimeError('wrong Figure 2 caption matched')
    if cap>0 and body[cap-1].xpath('.//w:drawing|.//w:pict',namespaces=NS): return False
    body.insert(cap,newp)
    return True

def append_free_listeners_to_toc(body):
    toc=body.find('w:tbl',NS)
    if toc is None: raise RuntimeError('TOC table missing')
    heading='SPECIAL THANKS FOR ACTIVE PARTICIPATION IN THE SCIENTIFIC AND PRACTICAL CONFERENCE ARE EXTENDED TO THE FOLLOWING PARTICIPANTS:'
    names=', '.join(name for name,_ in LISTENERS)
    # remove stale listener rows if rerun
    rows=toc.findall('w:tr',NS)
    for tr in list(rows):
        upper=p_text(tr).upper()
        if 'FREE LISTENERS' in upper or 'SPECIAL THANKS FOR ACTIVE PARTICIPATION' in upper:
            idx=toc.index(tr)
            for x in list(toc)[idx:]:
                if x.tag==q('tr'): toc.remove(x)
            break
    rows=toc.findall('w:tr',NS)
    sec_template=next(tr for tr in rows if len(tr.findall('w:tc',NS))==1)
    author_template=next(tr for tr in rows if len(tr.findall('w:tc',NS))==3 and p_text(tr.findall('w:tc',NS)[0]).endswith('.'))
    sec=copy.deepcopy(sec_template); set_cell_text(sec.find('w:tc',NS),heading,'TabSEC'); toc.append(sec)
    tr=copy.deepcopy(author_template); cells=tr.findall('w:tc',NS)
    set_cell_text(cells[0],'','TabTaitl'); set_cell_text(cells[1],names,'TabPIP'); set_cell_text(cells[2],'','TabTaitl'); toc.append(tr)
    return 2

def patch_doc(src,out):
    work=Path(tempfile.mkdtemp(prefix='v32_'))
    log={}
    try:
        with zipfile.ZipFile(src) as z:z.extractall(work)
        dp=work/'word/document.xml'; root=etree.parse(str(dp)).getroot(); body=root.find('w:body',NS)
        tail=find_tail_start(body)
        starts=article_starts(body,tail)
        log['standalone_pagebreak_paragraphs_removed']=remove_standalone_breaks(body,starts[0],tail)
        tail=find_tail_start(body)
        log['blank_paragraphs_removed_before_article_starts']=remove_blank_before_article_starts(body,tail)
        tail=find_tail_start(body); starts=article_starts(body,tail)
        add_pagebreak_before_articles(body,starts)
        log['pageBreakBefore_article_starts']=len(starts)
        # Sherbon body leading spaces / space-only pseudo-indent paragraphs.
        sher_start=next(i for i,ch in enumerate(body) if ch.tag==q('p') and style(ch)=='11' and p_text(ch).startswith('THE IDENTITY OF THE IMAGES'))
        sher_end=next(i for i in range(sher_start+1,len(body)) if body[i].tag==q('p') and style(body[i])=='REF-TITLE')
        removed=0; deleted=0
        for p in list(body[sher_start+1:sher_end]):
            if p.tag!=q('p'): continue
            raw=''.join(p.xpath('.//w:t/text()',namespaces=NS))
            if raw and not raw.strip(): body.remove(p); deleted+=1; continue
            removed+=strip_leading_spaces_preserve_runs(p)
        log['sherbon_leading_spaces_removed']=removed;log['sherbon_space_only_paragraphs_removed']=deleted
        log['todorova_figure2_restored']=restore_todorova_figure2(work,root,body)
        log['toc_listener_rows_added']=append_free_listeners_to_toc(body)
        etree.ElementTree(root).write(str(dp),encoding='UTF-8',xml_declaration=True,standalone=True)
        with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
            for p in work.rglob('*'):
                if p.is_file():z.write(p,p.relative_to(work).as_posix())
        return log
    finally: shutil.rmtree(work,ignore_errors=True)

def render(doc,outdir):
    if outdir.exists(): shutil.rmtree(outdir)
    subprocess.run(['python',RENDER,str(doc),'--output_dir',str(outdir),'--emit_pdf'],check=True)
    return next(outdir.glob('*.pdf'))

def pdf_pages_text(pdf):
    txt=pdf.with_suffix('.txt')
    subprocess.run(['pdftotext','-layout',str(pdf),str(txt)],check=True)
    return txt.read_text(errors='ignore').split('\f')[:-1]

def toc_titles(doc):
    with zipfile.ZipFile(doc) as z:root=etree.fromstring(z.read('word/document.xml'))
    toc=root.find('.//w:body/w:tbl',NS); rows=toc.findall('w:tr',NS)
    items=[]
    for i,tr in enumerate(rows):
        cells=tr.findall('w:tc',NS)
        if len(cells)==3:
            n=p_text(cells[0]); author=p_text(cells[1]); pg=p_text(cells[2])
            if re.fullmatch(r'\d+\.',n):
                title=''
                if i+1<len(rows):
                    c2=rows[i+1].findall('w:tc',NS)
                    if len(c2)==3 and not p_text(c2[0]): title=p_text(c2[1])
                if int(n[:-1])<=24: items.append((int(n[:-1]),author,title,pg))
    return items

def normalized(s):return re.sub(r'\s+',' ',s).strip().lower()

def derive_pages(doc,pdf):
    pages=pdf_pages_text(pdf)
    toc_end=0
    for i,p in enumerate(pages,1):
        if 'Olena Zorczykowska' in p: toc_end=max(toc_end,i)
    if not toc_end: raise RuntimeError('free listener TOC end not found')
    mapping={}
    for num,author,title,old in toc_titles(doc):
        key=normalized(title)
        candidates=[]
        for i,p in enumerate(pages,1):
            if i<=toc_end: continue
            if key and key in normalized(p): candidates.append(i)
        if not candidates:
            # author fallback
            first_author=normalized(author.split(',')[0])
            candidates=[i for i,p in enumerate(pages,1) if i>toc_end and first_author in normalized(p)]
        if not candidates: raise RuntimeError(f'page not found for {num} {title}')
        physical=min(candidates); mapping[num]={'physical':physical,'internal':physical-3,'title':title,'author':author}
    return mapping,toc_end,len(pages)

def update_toc_pages(src,out,mapping):
    work=Path(tempfile.mkdtemp(prefix='v32_toc_'))
    try:
        with zipfile.ZipFile(src) as z:z.extractall(work)
        dp=work/'word/document.xml';root=etree.parse(str(dp)).getroot();toc=root.find('.//w:body/w:tbl',NS)
        for tr in toc.findall('w:tr',NS):
            cells=tr.findall('w:tc',NS)
            if len(cells)!=3:continue
            n=p_text(cells[0])
            if re.fullmatch(r'\d+\.',n) and int(n[:-1]) in mapping:
                set_cell_text(cells[2],str(mapping[int(n[:-1])]['internal']),'TabTaitl')
        etree.ElementTree(root).write(str(dp),encoding='UTF-8',xml_declaration=True,standalone=True)
        with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
            for p in work.rglob('*'):
                if p.is_file():z.write(p,p.relative_to(work).as_posix())
    finally:shutil.rmtree(work,ignore_errors=True)

def structural_audit(doc):
    with zipfile.ZipFile(doc) as z:
        root=etree.fromstring(z.read('word/document.xml'));body=root.find('w:body',NS)
        rels=etree.fromstring(z.read('word/_rels/document.xml.rels'))
        media=set(n.split('/')[-1] for n in z.namelist() if n.startswith('word/media/'))
        broken=[]
        for rel in rels:
            t=rel.get('Target','')
            if t.startswith('media/') and Path(t).name not in media:broken.append(t)
        sect=len(root.xpath('//w:sectPr',namespaces=NS))
        tail=find_tail_start(body);starts=article_starts(body,tail)
        pbb=sum(1 for s in starts if body[s].find('w:pPr/w:pageBreakBefore',NS) is not None)
        standalone=sum(1 for p in body if is_standalone_pagebreak(p))
        # Todorova drawings in range
        ts=next(i for i,ch in enumerate(body) if ch.tag==q('p') and style(ch)=='11' and p_text(ch).startswith('ОЦІНКА ХАРАКТЕРИСТИК МАКСИМАЛЬНОГО СТОКУ'))
        te=next(i for i in range(ts+1,len(body)) if body[i].tag==q('p') and style(body[i])=='REF-TITLE')
        tod_draw=sum(len(ch.xpath('.//w:drawing|.//w:pict',namespaces=NS)) for ch in body[ts:te] if ch.tag==q('p'))
        toc=root.find('.//w:body/w:tbl',NS);listener_present='SPECIAL THANKS FOR ACTIVE PARTICIPATION' in p_text(toc).upper()
        return {'sections':sect,'article_starts':len(starts),'article_starts_with_pageBreakBefore':pbb,'standalone_pagebreak_paragraphs':standalone,'broken_media_relationships':broken,'todorova_drawing_paragraphs':tod_draw,'free_listener_section_present':listener_present,'free_listener_names_present':sum(1 for n,_ in LISTENERS if n in p_text(toc))}

def main():
    report={'source':str(SRC),'stage':str(OUT_STAGE),'final':str(OUT_FINAL),'changes':patch_doc(SRC,OUT_STAGE)}
    stage_pdf=render(OUT_STAGE,RENDER_STAGE)
    mapping,toc_end,stage_pages=derive_pages(OUT_STAGE,stage_pdf)
    report['stage_render']={'pages':stage_pages,'toc_end_physical_page':toc_end,'article_pages':mapping}
    update_toc_pages(OUT_STAGE,OUT_FINAL,mapping)
    final_pdf=render(OUT_FINAL,RENDER_FINAL)
    mapping2,toc_end2,final_pages=derive_pages(OUT_FINAL,final_pdf)
    report['final_render']={'pages':final_pages,'toc_end_physical_page':toc_end2,'article_pages':mapping2}
    report['structural_audit']=structural_audit(OUT_FINAL)
    report['page_mapping_stable']=mapping==mapping2
    report['status']='PASS' if report['page_mapping_stable'] and not report['structural_audit']['broken_media_relationships'] and report['structural_audit']['todorova_drawing_paragraphs']>=2 and report['structural_audit']['free_listener_names_present']==6 and report['structural_audit']['sections']==3 and report['structural_audit']['article_starts_with_pageBreakBefore']==24 and report['structural_audit']['standalone_pagebreak_paragraphs']==0 else 'FAIL'
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
