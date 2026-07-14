#!/usr/bin/env python3
from __future__ import annotations
import copy, json, re, shutil, tempfile, zipfile
from pathlib import Path
from lxml import etree

W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
NS={'w':W,'r':R}
q=lambda x:f'{{{W}}}{x}'
XMLSPACE='{http://www.w3.org/XML/1998/namespace}space'

SRC=Path('/mnt/data/JOURNAL_136_FULL_RELEASE_v30.docx')
TEMPLATE=Path('/mnt/data/ETALON-JOURNAL.docx')
OUT=Path('/mnt/data/JOURNAL_136_FULL_RELEASE_v31.docx')
REPORT=Path('/mnt/data/JOURNAL_136_FULL_RELEASE_v31_PATCH_REPORT.json')

FIG_RE=re.compile(r'^\s*(?:ри[сc]\.?|рисунок|мал\.?|малюнок|fig\.?|figure|abb\.?|abbildung|agd)\s*\d+\b',re.I)
TABLE_INLINE_RE=re.compile(r'^\s*((?:таблиця|table|tabelle)\s*\d+[A-Za-zА-Яа-яІіЇїЄєҐґ-]*)\s*(?:[-–—:])\s*(.+?)\s*$',re.I)
TABLE_LABEL_RE=re.compile(r'^\s*(?:таблиця|table|tabelle)\s*(?:\d+[A-Za-zА-Яа-яІіЇїЄєҐґ-]*)?\.?\s*$',re.I)
ANN_RE=re.compile(r'^\s*(?:Анотац(?:ія|iя)|Abstract|Annotation)\s*[.:]',re.I)
KW_RE=re.compile(r'^\s*(?:Ключові\s+слова|Key\s*words?|Keywords?)\s*:',re.I)
REF_MARKER_RE=re.compile(r'^\s*(?:список\s+використаних\s+джерел|список\s+використаної\s+літератури|список\s+літератури|література|references?|bibliography|literaturverzeichnis|quellenverzeichnis)\s*:?\s*$',re.I)
MANUAL_NUM_RE=re.compile(r'^\s*(?:\(?\d{1,3}\)?[.)]|[-–—•▪◦])\s*')
URL_RE=re.compile(r'https?://',re.I)
YEAR_RE=re.compile(r'\b(?:19|20)\d{2}\b')

TARGET_SOURCES={
    'ANTIVIRAL PROTEIN KINASE CK2 INHIBITORS': Path('/mnt/data/136_safe/059_b8690975.docx'),
    'АНАЛІЗ РЕЗУЛЬТАТІВ ЛІЦЕНЗІЙНОГО ІНТЕГРОВАНОГО ІСПИТУ «КРОК-3» ЯК ІНДИКАТОР ЕФЕКТИВНОСТІ ПІСЛЯДИПЛОМНОЇ ПІДГОТОВКИ ЛІКАРІВ-ІНТЕРНІВ ЗІ СПЕЦІАЛЬНОСТІ «ПЕДІАТРІЯ»': Path('/mnt/data/136_safe/108_b4b2fb39.docx'),
}

def norm(s:str)->str:
    return re.sub(r'\s+',' ',(s or '').replace('\u00a0',' ')).strip()

def p_text(p, nested=True):
    if nested:
        return norm(''.join(p.xpath('.//w:t/text()',namespaces=NS)))
    # exclude text inside textboxes
    parts=[]
    for t in p.xpath('.//w:t[not(ancestor::w:txbxContent)]',namespaces=NS):
        parts.append(t.text or '')
    return norm(''.join(parts))

def get_ppr(p,create=True):
    ppr=p.find(q('pPr'))
    if ppr is None and create:
        ppr=etree.Element(q('pPr'));p.insert(0,ppr)
    return ppr

def get_style(p):
    x=p.find('w:pPr/w:pStyle',NS)
    return x.get(q('val')) if x is not None else ''

def set_style(p,sid):
    ppr=get_ppr(p)
    x=ppr.find(q('pStyle'))
    if x is None:
        x=etree.Element(q('pStyle'));ppr.insert(0,x)
    x.set(q('val'),sid)

def set_jc(p,val):
    ppr=get_ppr(p);x=ppr.find(q('jc'))
    if x is None:x=etree.SubElement(ppr,q('jc'))
    x.set(q('val'),val)

def set_spacing(p,line='240',before='0',after='0'):
    ppr=get_ppr(p);x=ppr.find(q('spacing'))
    if x is None:x=etree.SubElement(ppr,q('spacing'))
    x.set(q('before'),before);x.set(q('after'),after);x.set(q('line'),line);x.set(q('lineRule'),'auto')

def set_firstline0(p):
    ppr=get_ppr(p);x=ppr.find(q('ind'))
    if x is None:x=etree.SubElement(ppr,q('ind'))
    x.set(q('firstLine'),'0')
    x.attrib.pop(q('hanging'),None)

def set_keep_next(p,on=True):
    ppr=get_ppr(p);x=ppr.find(q('keepNext'))
    if on and x is None: etree.SubElement(ppr,q('keepNext'))
    if not on and x is not None:ppr.remove(x)

def set_run_format(r,bold=None,italic=None,force_font=True):
    rpr=r.find(q('rPr'))
    if rpr is None:rpr=etree.Element(q('rPr'));r.insert(0,rpr)
    def boolprop(name,val):
        x=rpr.find(q(name))
        if val is None:return
        if x is None:x=etree.SubElement(rpr,q(name))
        if val:x.attrib.pop(q('val'),None)
        else:x.set(q('val'),'0')
    boolprop('b',bold);boolprop('bCs',bold);boolprop('i',italic);boolprop('iCs',italic)
    if force_font:
        fonts=rpr.find(q('rFonts'))
        if fonts is None:fonts=etree.Element(q('rFonts'));rpr.insert(0,fonts)
        for a in ('ascii','hAnsi','eastAsia','cs'):fonts.set(q(a),'Times New Roman')
        for tag in ('sz','szCs'):
            x=rpr.find(q(tag))
            if x is None:x=etree.SubElement(rpr,q(tag))
            x.set(q('val'),'22')

def clear_run_cosmetics(r,keep_bold=False,keep_italic=False):
    rpr=r.find(q('rPr'))
    if rpr is None:rpr=etree.Element(q('rPr'));r.insert(0,rpr)
    keep={'b','bCs'} if keep_bold else set()
    if keep_italic:keep|={'i','iCs'}
    for ch in list(rpr):
        if etree.QName(ch).localname not in keep:rpr.remove(ch)
    set_run_format(r,bold=True if keep_bold else None,italic=True if keep_italic else None)

def replace_plain_text(p,text,bold=False,italic=False):
    for ch in list(p):
        if ch.tag!=q('pPr'):p.remove(ch)
    r=etree.SubElement(p,q('r'));set_run_format(r,bold=bold,italic=italic)
    t=etree.SubElement(r,q('t'))
    if text.startswith(' ') or text.endswith(' '):t.set(XMLSPACE,'preserve')
    t.text=text

def make_p(text='',style='a0',jc=None,bold=False):
    p=etree.Element(q('p'));set_style(p,style);set_spacing(p);set_firstline0(p)
    if jc:set_jc(p,jc)
    if text:replace_plain_text(p,text,bold=bold)
    return p

def make_break_p():
    p=make_p('',style='a0')
    r=etree.SubElement(p,q('r'));br=etree.SubElement(r,q('br'));br.set(q('type'),'page')
    return p

def is_blank(p):return p.tag==q('p') and not p_text(p)
def is_break_only(p):
    return p.tag==q('p') and not p_text(p) and bool(p.xpath('.//w:br[@w:type="page"]',namespaces=NS))

def remove_page_breaks_in(el):
    count=0
    for br in list(el.xpath('.//w:br[@w:type="page"]',namespaces=NS)):
        br.getparent().remove(br);count+=1
    for pbb in list(el.xpath('.//w:pageBreakBefore',namespaces=NS)):
        pbb.getparent().remove(pbb);count+=1
    return count

def ensure_blank_before(body,idx):
    while idx>0 and is_blank(body[idx-1]) and not is_break_only(body[idx-1]):
        body.remove(body[idx-1]);idx-=1
    body.insert(idx,make_p())

def ensure_blank_after(body,idx):
    while idx+1<len(body) and is_blank(body[idx+1]) and not is_break_only(body[idx+1]):body.remove(body[idx+1])
    body.insert(idx+1,make_p())

def find_tail_start(body):
    for i,ch in enumerate(body):
        if ch.tag==q('p') and p_text(ch)=='SCIENCE IN THE MODERN WORLD' and i>1000:return i
    raise RuntimeError('tail start not found')

def get_template_middle_sect_p():
    with zipfile.ZipFile(TEMPLATE) as z:
        root=etree.fromstring(z.read('word/document.xml'));body=root.find('w:body',NS)
        for ch in body:
            s=ch.find('w:pPr/w:sectPr',NS) if ch.tag==q('p') else None
            if s is not None and s.find('w:footerReference',NS) is not None:
                return copy.deepcopy(ch)
    raise RuntimeError('template middle section paragraph not found')

def article_starts(body,article_end):
    udcs=[i for i,ch in enumerate(body[:article_end]) if ch.tag==q('p') and get_style(ch)=='UDC']
    starts=[]
    for ui in udcs:
        j=ui-1
        while j>=0 and is_blank(body[j]):j-=1
        if j>=0 and body[j].tag==q('p') and get_style(body[j])=='SECTION':starts.append(j)
        else:starts.append(ui)
    # dedupe preserving
    out=[]
    for x in starts:
        if x not in out:out.append(x)
    return out

def title_for_range(body,start,end):
    for ch in body[start:end]:
        if ch.tag==q('p') and get_style(ch)=='11':return p_text(ch)
    return ''

def bibliography_score(text):
    t=norm(text);score=0
    if URL_RE.search(t) or re.search(r'\bdoi\s*:',t,re.I):score+=3
    if YEAR_RE.search(t):score+=1
    if re.search(r'\b(?:№|vol\.?|том|вип\.?|с\.|p\.|pp\.|journal|press|видавництво|монограф|навчальн|зб\.)\b',t,re.I):score+=1
    if re.search(r'\b[А-ЯA-Z][а-яa-z]+\s+[А-ЯA-Z]\.',t):score+=1
    if re.search(r'\b(?:Київ|Львів|Одеса|Харків|Рівне|New York|London|Paris)\s*:',t,re.I):score+=1
    return score

def has_numpr(p):return p.find('w:pPr/w:numPr',NS) is not None

def new_reference_num(numbering_root):
    ids=[int(x.get(q('numId'))) for x in numbering_root.findall('w:num',NS) if (x.get(q('numId')) or '').isdigit()]
    nid=max(ids or [0])+1
    num=etree.Element(q('num'));num.set(q('numId'),str(nid))
    an=etree.SubElement(num,q('abstractNumId'));an.set(q('val'),'2')
    ov=etree.SubElement(num,q('lvlOverride'));ov.set(q('ilvl'),'0')
    st=etree.SubElement(ov,q('startOverride'));st.set(q('val'),'1')
    numbering_root.append(num)
    return str(nid)

def set_reference_num(p,nid):
    ppr=get_ppr(p);np=ppr.find(q('numPr'))
    if np is None:np=etree.SubElement(ppr,q('numPr'))
    for ch in list(np):np.remove(ch)
    il=etree.SubElement(np,q('ilvl'));il.set(q('val'),'0')
    ni=etree.SubElement(np,q('numId'));ni.set(q('val'),nid)

def normalize_reference_p(p,nid):
    txt=p_text(p)
    txt=MANUAL_NUM_RE.sub('',txt)
    replace_plain_text(p,txt,bold=False)
    set_style(p,'REFER');set_reference_num(p,nid);set_spacing(p);set_firstline0(p)

def language_heading(title,article_ps):
    sample=' '.join([title]+[p_text(p) for p in article_ps[:6]])
    latin=sum(c.isalpha() and ord(c)<128 for c in sample);cyr=sum('А'<=c.upper()<='Я' or c in 'ІіЇїЄєҐґ' for c in sample)
    return 'REFERENCES' if latin>cyr*1.5 else 'СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ:'

def infer_unmarked_references(body,start,end,numbering_root,log):
    ps=[(i,ch) for i,ch in enumerate(body[start:end],start) if ch.tag==q('p')]
    if any(get_style(p)=='REF-TITLE' or REF_MARKER_RE.fullmatch(p_text(p) or '') for _,p in ps):return False
    nonblank=[(i,p) for i,p in ps if p_text(p)]
    if len(nonblank)<4:return False
    cand=[]
    for i,p in reversed(nonblank):
        t=p_text(p); score=bibliography_score(t)
        if has_numpr(p) or MANUAL_NUM_RE.match(t) or score>=2:
            cand.append((i,p,score));continue
        break
    cand=list(reversed(cand))
    if len(cand)<2:return False
    # must be in final 45% of article and have clear bibliography signals
    if cand[0][0] < start + int((end-start)*0.55):return False
    scores=[x[2] for x in cand]
    if sum(s>=1 for s in scores)<max(2,len(cand)//2):return False
    first_idx=cand[0][0]
    # collapse blanks before candidate
    while first_idx>start and is_blank(body[first_idx-1]):body.remove(body[first_idx-1]);first_idx-=1;end-=1
    title=title_for_range(body,start,end)
    heading=make_p(language_heading(title,[p for _,p,_ in cand]),style='REF-TITLE',jc='center',bold=True)
    body.insert(first_idx,make_p());body.insert(first_idx+1,heading);body.insert(first_idx+2,make_p())
    nid=new_reference_num(numbering_root)
    # candidate nodes keep identity despite insertion
    for _,p,_ in cand:normalize_reference_p(p,nid)
    log.append({'title':title,'count':len(cand),'heading':p_text(heading),'numId':nid})
    return True

def ensure_existing_reference_blocks(body,starts,tail_start,numbering_root,log):
    # recompute ranges and normalize entries after headings. Existing unique numIds remain unless absent.
    bounds=starts+[tail_start]
    for a,b in zip(bounds,bounds[1:]):
        heading_idx=None
        for i in range(a,b):
            ch=body[i]
            if ch.tag==q('p') and (get_style(ch)=='REF-TITLE' or REF_MARKER_RE.fullmatch(p_text(ch) or '')):
                heading_idx=i;break
        if heading_idx is None:continue
        hp=body[heading_idx];set_style(hp,'REF-TITLE');set_jc(hp,'center');set_spacing(hp);set_firstline0(hp)
        # ensure canonical language by article language, while preserving German accepted headings
        ht=p_text(hp);title=title_for_range(body,a,b)
        if not re.search(r'literatur|quellen',ht,re.I):
            canonical=language_heading(title,[]);replace_plain_text(hp,canonical,bold=True)
        ensure_blank_before(body,heading_idx);heading_idx+=1
        ensure_blank_after(body,heading_idx)
        # indices shifted: locate heading object again
        heading_idx=body.index(hp)
        refs=[]
        for i in range(heading_idx+1,len(body)):
            if i>=b+3:break
            ch=body[i]
            if ch.tag!=q('p'):break
            t=p_text(ch)
            if not t:continue
            if get_style(ch) in {'SECTION','UDC','AUTOR','11'}:break
            refs.append(ch)
        if not refs:continue
        # use first existing num id or new
        nid=None
        for p in refs:
            ni=p.find('w:pPr/w:numPr/w:numId',NS)
            if ni is not None:nid=ni.get(q('val'));break
        if nid is None:nid=new_reference_num(numbering_root)
        for p in refs:normalize_reference_p(p,nid)
        log.append({'title':title,'count':len(refs),'numId':nid})

def style_inner_shapes(root,log):
    fig_count=table_count=cell_count=0;split_outer=0
    for tx in root.xpath('//w:txbxContent',namespaces=NS):
        tables=tx.xpath('.//w:tbl',namespaces=NS)
        direct_ps=tx.xpath('./w:p',namespaces=NS)
        if tables:
            # title is first nonempty direct paragraph before first table
            for p in direct_ps:
                t=p_text(p)
                if t:
                    set_style(p,'af6');set_jc(p,'center');set_spacing(p);set_firstline0(p);set_keep_next(p)
                    for r in p.xpath('.//w:r',namespaces=NS):set_run_format(r,bold=True)
                    table_count+=1;break
            for p in tx.xpath('.//w:tbl//w:p',namespaces=NS):
                set_style(p,'TABLETEXT');set_spacing(p);set_firstline0(p)
                for r in p.xpath('.//w:r',namespaces=NS):set_run_format(r)
                cell_count+=1
        else:
            for p in direct_ps:
                t=p_text(p)
                if FIG_RE.match(t):
                    set_style(p,'af6');set_jc(p,'center');set_spacing(p);set_firstline0(p)
                    for r in p.xpath('.//w:r',namespaces=NS):set_run_format(r,bold=True)
                    fig_count+=1
    # Outer paragraphs containing textbox tables are object containers, not figures. Split any direct Table N text.
    for p in root.xpath('//w:p[.//w:txbxContent//w:tbl]',namespaces=NS):
        set_style(p,'a0');set_jc(p,'center');set_spacing(p);set_firstline0(p)
        direct=p_text(p,nested=False)
        if re.match(r'^\s*(?:Таблиця|Table|Tabelle)\s*\d+',direct,re.I):
            m=re.match(r'^\s*((?:Таблиця|Table|Tabelle)\s*\d+[A-Za-zА-Яа-яІіЇїЄєҐґ-]*\.?)(.*)$',direct,re.I)
            if m:
                label=m.group(1).rstrip('.')
                # remove direct text nodes outside txbx
                for t in p.xpath('.//w:t[not(ancestor::w:txbxContent)]',namespaces=NS):t.text=''
                parent=p.getparent();idx=parent.index(p)
                lp=make_p(label,style='a0',jc='right',bold=True);set_keep_next(lp)
                parent.insert(idx,lp);split_outer+=1
    log.update({'figure_captions_in_textboxes':fig_count,'table_titles_in_textboxes':table_count,'table_cell_paragraphs':cell_count,'outer_table_labels_split':split_outer})

def split_direct_table_captions(body,log):
    count=0
    i=0
    while i<len(body):
        ch=body[i]
        if ch.tag==q('p'):
            m=TABLE_INLINE_RE.match(p_text(ch))
            if m and i+1<len(body) and body[i+1].tag==q('tbl'):
                label=m.group(1).rstrip('.');title=m.group(2)
                replace_plain_text(ch,label,bold=True);set_style(ch,'a0');set_jc(ch,'right');set_spacing(ch);set_firstline0(ch);set_keep_next(ch)
                tp=make_p(title,style='af6',jc='center',bold=True);set_keep_next(tp)
                body.insert(i+1,tp)
                # one blank before label
                ensure_blank_before(body,i);i+=2
                count+=1
        i+=1
    log['direct_table_caption_splits']=count

def ensure_table_spacing(body,article_start,article_end,log):
    count=0
    i=article_start
    while i<min(article_end,len(body)):
        if body[i].tag==q('tbl'):
            # Caption block is normally: label paragraph, title paragraph, table.
            first=i
            j=i-1
            while j>=article_start and is_blank(body[j]):
                # blanks between title and table are always removed
                body.remove(body[j]);i-=1;article_end-=1;j-=1
            if j>=article_start and body[j].tag==q('p'):
                k=j-1
                if get_style(body[j])=='af6':
                    first=j
                    if k>=article_start and body[k].tag==q('p') and TABLE_LABEL_RE.match(p_text(body[k])):first=k
                elif k>=article_start and body[k].tag==q('p') and TABLE_LABEL_RE.match(p_text(body[k])):
                    # unstyled title followed by a recognized label
                    first=k
                    set_style(body[j],'af6');set_jc(body[j],'center');set_spacing(body[j]);set_firstline0(body[j]);set_keep_next(body[j])
                    for r in body[j].xpath('.//w:r',namespaces=NS):set_run_format(r,bold=True)
                elif TABLE_LABEL_RE.match(p_text(body[j])):
                    first=j
            # exactly one blank before entire caption/table cluster
            while first>article_start and is_blank(body[first-1]) and not is_break_only(body[first-1]):
                body.remove(body[first-1]);first-=1;i-=1;article_end-=1
            body.insert(first,make_p());i+=1;article_end+=1;count+=1
            # normalize table cells only
            table_node=body[i] if body[i].tag==q('tbl') else next((x for x in body[first:i+3] if x.tag==q('tbl')),None)
            if table_node is not None:
                for p in table_node.xpath('.//w:p',namespaces=NS):
                    set_style(p,'TABLETEXT');set_spacing(p);set_firstline0(p)
        i+=1
    log['direct_tables_spaced']=count

def annotation_keyword_spacing(body,starts,tail_start,log):
    fixed=0
    bounds=starts+[tail_start]
    for a,b in zip(bounds,bounds[1:]):
        ann=kw=None
        for i in range(a,b):
            if body[i].tag!=q('p'):continue
            t=p_text(body[i])
            if ann is None and ANN_RE.match(t):ann=body[i]
            if kw is None and KW_RE.match(t):kw=body[i]
        if ann is not None and kw is not None:
            ai=body.index(ann);ki=body.index(kw)
            # remove blanks between annotation and keywords
            j=ai+1
            while j<ki:
                if is_blank(body[j]):body.remove(body[j]);ki-=1;fixed+=1
                else:j+=1
            # exactly one blank after keywords
            ki=body.index(kw)
            while ki+1<len(body) and is_blank(body[ki+1]) and not is_break_only(body[ki+1]):body.remove(body[ki+1]);fixed+=1
            body.insert(ki+1,make_p());fixed+=1
    log['annotation_keyword_spacing_ops']=fixed

def effective_style_maps(path):
    with zipfile.ZipFile(path) as z:
        styles_root=etree.fromstring(z.read('word/styles.xml'));doc_root=etree.fromstring(z.read('word/document.xml'))
    styles={s.get(q('styleId')):s for s in styles_root.findall('w:style',NS)}
    def prop_from_style(sid,prop):
        seen=set()
        while sid and sid not in seen:
            seen.add(sid);s=styles.get(sid)
            if s is None:break
            x=s.find(f'w:rPr/w:{prop}',NS)
            if x is not None:
                v=x.get(q('val'));return v not in ('0','false','off')
            b=s.find('w:basedOn',NS);sid=b.get(q('val')) if b is not None else None
        return False
    def run_bool(r,p_sid,prop):
        x=r.find(f'w:rPr/w:{prop}',NS)
        if x is not None:
            v=x.get(q('val'));return v not in ('0','false','off')
        rs=r.find('w:rPr/w:rStyle',NS)
        if rs is not None:
            val=prop_from_style(rs.get(q('val')),prop)
            if val:return True
        return prop_from_style(p_sid,prop)
    mapping={}
    for p in doc_root.xpath('//w:body/w:p',namespaces=NS):
        text=''.join(p.xpath('.//w:t/text()',namespaces=NS))
        if not text:continue
        ps=p.find('w:pPr/w:pStyle',NS);sid=ps.get(q('val')) if ps is not None else ''
        seg=[]
        for r in p.findall('w:r',NS):
            rt=''.join(r.xpath('.//w:t/text()',namespaces=NS))
            if not rt:continue
            seg.append((rt,run_bool(r,sid,'b'),run_bool(r,sid,'i')))
        if seg and ''.join(x[0] for x in seg)==text:mapping[norm(text)]=(text,seg)
    return mapping

def rebuild_runs_from_segments(p,text,segments):
    if ''.join(x[0] for x in segments)!=text:return False
    for ch in list(p):
        if ch.tag!=q('pPr'):p.remove(ch)
    for s,b,i in segments:
        r=etree.SubElement(p,q('r'));set_run_format(r,bold=b,italic=i)
        t=etree.SubElement(r,q('t'))
        if s.startswith(' ') or s.endswith(' '):t.set(XMLSPACE,'preserve')
        t.text=s
    return True

def restore_source_emphasis(body,starts,tail_start,log):
    restored=[];bounds=starts+[tail_start]
    title_to_range={title_for_range(body,a,b):(a,b) for a,b in zip(bounds,bounds[1:])}
    for title,src in TARGET_SOURCES.items():
        if title not in title_to_range:continue
        mapping=effective_style_maps(src);a,b=title_to_range[title]
        for idx in range(a,b):
            p=body[idx]
            if p.tag!=q('p') or p.xpath('.//w:drawing|.//w:pict|.//w:fldChar',namespaces=NS):continue
            t=p_text(p)
            if not t or ANN_RE.match(t) or KW_RE.match(t) or get_style(p) in {'REF-TITLE','REFER','UDC','AUTOR','pip','11'}:continue
            item=mapping.get(norm(t))
            if not item:continue
            raw,segs=item
            if raw==''.join(p.xpath('.//w:t/text()',namespaces=NS)) and any(bd or it for _,bd,it in segs):
                if rebuild_runs_from_segments(p,raw,segs):restored.append({'title':title,'paragraph':t[:120]})
    log['source_emphasis_restored']=restored

def normalize_figure_outer_paragraphs(body,article_start,article_end,log):
    n=0
    for p in list(body[article_start:article_end]):
        if p.tag!=q('p'):continue
        if not p.xpath('.//w:drawing or .//w:pict',namespaces=NS):continue
        if p.xpath('.//w:txbxContent//w:tbl',namespaces=NS):continue
        set_style(p,'ad');set_jc(p,'center');set_spacing(p);set_firstline0(p);n+=1
    log['figure_object_paragraphs_styled']=n

def main():
    work=Path(tempfile.mkdtemp(prefix='v31_'))
    try:
        with zipfile.ZipFile(SRC) as z:z.extractall(work)
        doc_path=work/'word/document.xml';num_path=work/'word/numbering.xml'
        root=etree.parse(str(doc_path)).getroot();body=root.find('w:body',NS)
        numbering=etree.parse(str(num_path)).getroot()
        report={'source':str(SRC),'output':str(OUT),'changes':{}}
        changes=report['changes']
        # Article region ends at final tail.
        tail=find_tail_start(body)
        # Restore template section break immediately before protected final tail.
        # Remove old blank spacer paragraphs before tail.
        while tail>0 and is_blank(body[tail-1]):body.remove(body[tail-1]);tail-=1
        # remove any existing sectPr paragraph here to avoid duplicates
        if tail>0 and body[tail-1].tag==q('p') and body[tail-1].find('w:pPr/w:sectPr',NS) is not None:body.remove(body[tail-1]);tail-=1
        sectp=get_template_middle_sect_p();body.insert(tail,sectp);tail+=1
        changes['page_number_section_restored']=True
        # Remove internal author page breaks in article region.
        removed=0
        for ch in list(body[72:tail]):removed+=remove_page_breaks_in(ch)
        # remove empty paragraphs that became page-break-only empties, except regular contract blanks
        for ch in list(body[72:tail]):
            if ch.tag==q('p') and not p_text(ch) and len(ch.xpath('.//w:drawing|.//w:pict|.//w:object|.//w:tbl',namespaces=NS))==0:
                # keep ordinary blanks for now; cleanup only those with empty runs generated by break removal
                if ch.find('w:pPr/w:pStyle',NS) is not None and ch.find('w:pPr/w:pStyle',NS).get(q('val')) not in {'a0','ad'}:continue
        changes['internal_page_breaks_removed']=removed
        # Recompute start/tail and install explicit break-only paragraphs before every article after first.
        tail=find_tail_start(body)
        starts=article_starts(body,tail)
        inserted=0
        # reverse order avoids index drift
        for start in reversed(starts[1:]):
            # remove blank/break paragraphs immediately before start
            while start>0 and body[start-1].tag==q('p') and (is_blank(body[start-1]) or is_break_only(body[start-1])):
                body.remove(body[start-1]);start-=1
            body.insert(start,make_break_p());inserted+=1
        changes['article_boundary_page_breaks_inserted']=inserted
        # Recompute after insertion.
        tail=find_tail_start(body);starts=article_starts(body,tail)
        annotation_keyword_spacing(body,starts,tail,changes)
        split_direct_table_captions(body,changes)
        tail=find_tail_start(body);starts=article_starts(body,tail)
        ensure_table_spacing(body,starts[0],tail,changes)
        style_inner_shapes(root,changes)
        tail=find_tail_start(body);starts=article_starts(body,tail)
        normalize_figure_outer_paragraphs(body,starts[0],tail,changes)
        # Existing references then infer missing unmarked tails.
        tail=find_tail_start(body);starts=article_starts(body,tail)
        existing=[];ensure_existing_reference_blocks(body,starts,tail,numbering,existing);changes['existing_reference_blocks_normalized']=existing
        tail=find_tail_start(body);starts=article_starts(body,tail)
        inferred=[]
        # reverse to avoid index shifts affecting later ranges
        bounds=starts+[tail]
        for a,b in reversed(list(zip(bounds,bounds[1:]))):infer_unmarked_references(body,a,b,numbering,inferred)
        changes['unmarked_reference_blocks_inferred']=inferred
        # Recompute and restore source emphasis.
        tail=find_tail_start(body);starts=article_starts(body,tail)
        restore_source_emphasis(body,starts,tail,changes)
        changes['hnysiuk_blank_before_table']=True
        # Write XMLs.
        etree.ElementTree(root).write(str(doc_path),encoding='UTF-8',xml_declaration=True,standalone=True)
        etree.ElementTree(numbering).write(str(num_path),encoding='UTF-8',xml_declaration=True,standalone=True)
        # Pack.
        with zipfile.ZipFile(OUT,'w',zipfile.ZIP_DEFLATED) as z:
            for p in work.rglob('*'):
                if p.is_file():z.write(p,p.relative_to(work).as_posix())
        REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(report,ensure_ascii=False,indent=2))
    finally:
        shutil.rmtree(work,ignore_errors=True)
if __name__=='__main__':main()
