from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree
from pathlib import Path
import shutil, os, re

W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
NS={'w':W,'r':R}

def q(tag): return f'{{{W}}}{tag}'

def text_of(el):
    return ''.join(el.xpath('.//w:t/text()', namespaces=NS)).strip()

def pstyle(p):
    ps=p.find('./w:pPr/w:pStyle', NS)
    return ps.get(q('val')) if ps is not None else None

def ensure_ppr(p):
    ppr=p.find('w:pPr', NS)
    if ppr is None:
        ppr=etree.Element(q('pPr'))
        p.insert(0,ppr)
    return ppr

def set_pstyle(p, val):
    ppr=ensure_ppr(p)
    ps=ppr.find('w:pStyle', NS)
    if ps is None:
        ps=etree.Element(q('pStyle')); ppr.insert(0,ps)
    ps.set(q('val'), val)

def remove_children(ppr, names):
    for nm in names:
        for e in ppr.findall(f'w:{nm}', NS):
            ppr.remove(e)

def set_ind_zero(p):
    ppr=ensure_ppr(p)
    remove_children(ppr, ['ind'])
    ind=etree.Element(q('ind')); ind.set(q('firstLine'),'0')
    ppr.append(ind)

def set_spacing(p, line='240', before='0', after='0'):
    ppr=ensure_ppr(p)
    remove_children(ppr, ['spacing'])
    sp=etree.Element(q('spacing')); sp.set(q('line'), line); sp.set(q('lineRule'),'auto'); sp.set(q('before'), before); sp.set(q('after'), after)
    ppr.append(sp)

def set_jc(p, val):
    ppr=ensure_ppr(p)
    remove_children(ppr, ['jc'])
    jc=etree.Element(q('jc')); jc.set(q('val'), val); ppr.append(jc)

def clear_para_direct(p, keep=('pStyle','numPr','sectPr','pageBreakBefore')):
    ppr=p.find('w:pPr', NS)
    if ppr is None: return
    for ch in list(ppr):
        lname=etree.QName(ch).localname
        if lname not in keep:
            ppr.remove(ch)

def clear_run_formatting(p):
    # convert hyperlinks to normal runs retaining text
    for hyp in list(p.findall('.//w:hyperlink', NS)):
        parent=hyp.getparent(); idx=parent.index(hyp)
        for child in list(hyp):
            parent.insert(idx, child); idx += 1
        parent.remove(hyp)
    for r in p.findall('.//w:r', NS):
        rpr=r.find('w:rPr', NS)
        if rpr is not None:
            r.remove(rpr)

def set_all_runs_font(p, size=22, bold=None, italic=None):
    for r in p.findall('.//w:r', NS):
        rpr=r.find('w:rPr', NS)
        if rpr is None:
            rpr=etree.Element(q('rPr')); r.insert(0,rpr)
        # remove existing b/i/sz/underline/color/shading
        for nm in ['b','bCs','i','iCs','sz','szCs','u','color','highlight','shd','rStyle']:
            for e in rpr.findall(f'w:{nm}', NS): rpr.remove(e)
        sz=etree.Element(q('sz')); sz.set(q('val'), str(size)); rpr.append(sz)
        szcs=etree.Element(q('szCs')); szcs.set(q('val'), str(size)); rpr.append(szcs)
        if bold is not None:
            b=etree.Element(q('b'))
            if not bold: b.set(q('val'),'0')
            rpr.insert(0,b)
        if italic is not None:
            i=etree.Element(q('i'))
            if not italic: i.set(q('val'),'0')
            rpr.insert(0,i)

def blank_para():
    p=etree.Element(q('p'))
    ppr=etree.Element(q('pPr'))
    sp=etree.Element(q('spacing')); sp.set(q('line'),'240'); sp.set(q('lineRule'),'auto'); sp.set(q('before'),'0'); sp.set(q('after'),'0')
    ind=etree.Element(q('ind')); ind.set(q('firstLine'),'0')
    ppr.append(sp); ppr.append(ind); p.append(ppr)
    return p

def is_blank(el):
    return el.tag==q('p') and text_of(el)=='' and len(el.xpath('.//w:drawing|.//w:pict', namespaces=NS))==0

def insert_blank_after(body, child):
    idx=body.index(child)
    if idx+1 < len(body) and is_blank(body[idx+1]):
        return False
    body.insert(idx+1, blank_para()); return True

def insert_blank_before(body, child):
    idx=body.index(child)
    if idx>0 and is_blank(body[idx-1]):
        return False
    body.insert(idx, blank_para()); return True

def set_style_outline(styles_root, style_id, level):
    st=styles_root.xpath(f'//w:style[@w:styleId="{style_id}"]', namespaces=NS)
    if not st: return False
    st=st[0]
    ppr=st.find('w:pPr', NS)
    if ppr is None:
        ppr=etree.Element(q('pPr'))
        # insert after name/basedOn etc before rPr if possible
        rpr=st.find('w:rPr', NS)
        if rpr is not None: st.insert(st.index(rpr), ppr)
        else: st.append(ppr)
    for e in ppr.findall('w:outlineLvl', NS): ppr.remove(e)
    if level is not None:
        ol=etree.Element(q('outlineLvl')); ol.set(q('val'), str(level)); ppr.append(ol)
    return True

def find_style_id_by_name(styles_root, name):
    for st in styles_root.xpath('//w:style', namespaces=NS):
        nm=st.find('w:name', NS)
        if nm is not None and nm.get(q('val'))==name:
            return st.get(q('styleId'))
    return None

def normalize_styles(styles_root):
    # TOC contract: only SECTION, AUTOR, Назва1 enter outlines. pip must not.
    set_style_outline(styles_root,'SECTION',0)
    set_style_outline(styles_root,'AUTOR',1)
    title_id=find_style_id_by_name(styles_root,'Назва1') or '11'
    set_style_outline(styles_root,title_id,2)
    set_style_outline(styles_root,'pip',None)
    # Force pip basedOn Normal to avoid inherited heading behavior
    st=styles_root.xpath('//w:style[@w:styleId="pip"]', namespaces=NS)
    if st:
        based=st[0].find('w:basedOn', NS)
        if based is None:
            based=etree.Element(q('basedOn')); st[0].insert(1,based)
        based.set(q('val'),'a0')

def make_new_num(numbering_root, base_abs='1'):
    existing=[int(n.get(q('numId'))) for n in numbering_root.xpath('//w:num', namespaces=NS) if n.get(q('numId')).isdigit()]
    new_id=str(max(existing+[0])+1)
    num=etree.Element(q('num')); num.set(q('numId'), new_id)
    absn=etree.Element(q('abstractNumId')); absn.set(q('val'), base_abs); num.append(absn)
    ov=etree.Element(q('lvlOverride')); ov.set(q('ilvl'),'0')
    st=etree.Element(q('startOverride')); st.set(q('val'),'1'); ov.append(st); num.append(ov)
    numbering_root.append(num)
    return new_id

def ensure_ref_numbering(p, numId):
    ppr=ensure_ppr(p)
    remove_children(ppr,['numPr','tabs','ind'])
    # pStyle first
    set_pstyle(p,'REFER')
    ppr=ensure_ppr(p)
    # find index after pStyle
    numPr=etree.Element(q('numPr'))
    ilvl=etree.Element(q('ilvl')); ilvl.set(q('val'),'0')
    nid=etree.Element(q('numId')); nid.set(q('val'),numId)
    numPr.append(ilvl); numPr.append(nid)
    # insert after pStyle if exists
    pstyle_el=ppr.find('w:pStyle', NS)
    insert_idx=ppr.index(pstyle_el)+1 if pstyle_el is not None else 0
    ppr.insert(insert_idx, numPr)
    set_spacing(p)
    set_jc(p,'both')

def clean_ref_para(p, numId):
    ensure_ref_numbering(p,numId)
    clear_run_formatting(p)
    set_all_runs_font(p, size=22, bold=False, italic=False)
    # remove literal tabs at text starts that came from manual lists
    for t in p.findall('.//w:t', NS):
        if t.text:
            t.text=t.text.replace('\t',' ').replace('  ',' ')

def normalize_table_cells(tbl):
    for p in tbl.xpath('.//w:p', namespaces=NS):
        set_pstyle(p,'TABLETEXT')
        clear_para_direct(p, keep=('pStyle',))
        set_ind_zero(p); set_spacing(p)
        clear_run_formatting(p)
        set_all_runs_font(p, size=22)

def normalize_document_xml(root, numbering_root):
    body=root.find('w:body', NS)
    children=list(body)
    # normalize all paragraphs/styles and table cells
    for el in list(body):
        if el.tag==q('tbl'):
            normalize_table_cells(el)
            continue
        if el.tag!=q('p'): continue
        txt=text_of(el)
        st=pstyle(el)
        # remove any direct outline except for the three TOC styles
        ppr=el.find('w:pPr', NS)
        if ppr is not None and st not in ('SECTION','AUTOR','11'):
            for ol in ppr.findall('w:outlineLvl', NS): ppr.remove(ol)
        if st=='pip':
            clear_para_direct(el, keep=('pStyle',))
            set_ind_zero(el); set_spacing(el)
        elif st=='SECTION':
            # exact style-driven, no extra pPr except pStyle / pageBreakBefore if present
            clear_para_direct(el, keep=('pStyle','pageBreakBefore'))
        elif st=='AUTOR':
            clear_para_direct(el, keep=('pStyle',))
        elif st=='UDC':
            clear_para_direct(el, keep=('pStyle',))
            set_ind_zero(el); set_spacing(el)
        elif st=='11':
            clear_para_direct(el, keep=('pStyle','pageBreakBefore'))
        elif st in ('ad','af6'):
            clear_para_direct(el, keep=('pStyle',))
            set_ind_zero(el); set_spacing(el); set_jc(el,'center')
        # table captions and source lines
        if re.match(r'^Таблиця\s*\d+\.?$', txt):
            set_pstyle(el,'a0')
            clear_para_direct(el, keep=('pStyle',))
            set_ind_zero(el); set_spacing(el); set_jc(el,'right')
            set_all_runs_font(el, size=22, bold=True)
        elif re.match(r'^Table\s*\d+\.?$', txt, re.I):
            clear_para_direct(el, keep=('pStyle',))
            set_ind_zero(el); set_spacing(el); set_jc(el,'right')
            set_all_runs_font(el, size=22, bold=True)
        elif txt.startswith('Джерело') or txt.startswith('Source'):
            clear_para_direct(el, keep=('pStyle',))
            set_ind_zero(el); set_spacing(el); set_jc(el,'left')
            set_all_runs_font(el, size=22, italic=True)
        elif st=='REF-TITLE' or txt.upper().startswith('СПИСОК ВИКОРИСТАН') or txt.upper().startswith('REFERENCES'):
            # canonical stamp
            for t in el.findall('.//w:t', NS):
                t.text = 'СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ:' if t is el.findall('.//w:t', NS)[0] else ''
            set_pstyle(el,'REF-TITLE')
            clear_para_direct(el, keep=('pStyle',))
            set_spacing(el); set_jc(el,'center')
            set_all_runs_font(el, size=22, bold=True)
        # possible table title: paragraph immediately after table number will be handled in second pass
    
    # table title paragraphs immediately after table numbers
    children=list(body)
    for i,el in enumerate(children[:-1]):
        if el.tag==q('p') and re.match(r'^Таблиця\s*\d+\.?$', text_of(el)):
            nxt=children[i+1]
            if nxt.tag==q('p') and text_of(nxt):
                clear_para_direct(nxt, keep=('pStyle',))
                set_ind_zero(nxt); set_spacing(nxt); set_jc(nxt,'center')
                set_all_runs_font(nxt, size=22, bold=True)
    
    # reference blocks: each block gets a fresh numbering from 1
    children=list(body); i=0
    while i < len(children):
        el=children[i]
        if el.tag==q('p') and (pstyle(el)=='REF-TITLE' or text_of(el).upper().startswith('СПИСОК ВИКОРИСТАН')):
            insert_blank_before(body, el)
            insert_blank_after(body, el)
            # refresh children after insertion; find the title's current index
            children=list(body); idx=children.index(el)
            # collect following reference paragraphs after optional blank
            j=idx+1
            if j < len(children) and is_blank(children[j]):
                j += 1
            ref_ps=[]
            while j < len(children):
                c=children[j]
                if c.tag!=q('p'): break
                tx=text_of(c); st=pstyle(c)
                if tx=='' or tx.startswith('SCIENCE') or st in ('SECTION','UDC','AUTOR','pip','11'):
                    break
                # Treat existing REFER or bibliography-looking paragraphs
                if st=='REFER' or re.match(r'^[A-ZА-ЯІЇЄҐ0-9][^\n]{10,}', tx):
                    ref_ps.append(c); j+=1
                else:
                    break
            numId=make_new_num(numbering_root, '1')
            for rp in ref_ps:
                clean_ref_para(rp, numId)
            children=list(body); i=idx+len(ref_ps)+2
            continue
        i += 1
    
    # spacing blanks after article titles, figure captions if no source, source lines
    children=list(body)
    for el in list(children):
        if el.tag!=q('p'): continue
        txt=text_of(el); st=pstyle(el)
        if st=='11':
            insert_blank_after(body, el)
        elif st=='af6':
            # add blank after caption only if next nonblank is not source
            idx=body.index(el); nxt=body[idx+1] if idx+1<len(body) else None
            if nxt is not None and not (nxt.tag==q('p') and text_of(nxt).startswith('Джерело')):
                insert_blank_after(body, el)
        elif txt.startswith('Джерело') or txt.startswith('Source'):
            insert_blank_after(body, el)
    return root

def patch_docx(src, dst):
    src=Path(src); dst=Path(dst)
    tmp=dst.with_suffix('.tmp.docx')
    with ZipFile(src,'r') as zin, ZipFile(tmp,'w',ZIP_DEFLATED) as zout:
        doc_root=None; styles_root=None; numbering_root=None
        for item in zin.infolist():
            data=zin.read(item.filename)
            if item.filename=='word/document.xml':
                doc_root=etree.fromstring(data)
                continue
            if item.filename=='word/styles.xml':
                styles_root=etree.fromstring(data)
                continue
            if item.filename=='word/numbering.xml':
                numbering_root=etree.fromstring(data)
                continue
            zout.writestr(item, data)
        if styles_root is None or doc_root is None or numbering_root is None:
            raise RuntimeError('missing core OOXML')
        normalize_styles(styles_root)
        normalize_document_xml(doc_root, numbering_root)
        zout.writestr('word/document.xml', etree.tostring(doc_root, xml_declaration=True, encoding='UTF-8', standalone='yes'))
        zout.writestr('word/styles.xml', etree.tostring(styles_root, xml_declaration=True, encoding='UTF-8', standalone='yes'))
        zout.writestr('word/numbering.xml', etree.tostring(numbering_root, xml_declaration=True, encoding='UTF-8', standalone='yes'))
    tmp.replace(dst)

if __name__=='__main__':
    pairs=[
        ('/mnt/data/ETALON_Hnysiuk_Motivation_11pt_single_BUSINESS_FIXED.docx','/mnt/data/ETALON_Hnysiuk_Motivation_11pt_single_BUSINESS_FIXED_v2.docx'),
        ('/mnt/data/ETALON_Soloviov_Halenko_Debretseni_11pt_single_BUSINESS_FIXED.docx','/mnt/data/ETALON_Soloviov_Halenko_Debretseni_11pt_single_BUSINESS_FIXED_v2.docx')
    ]
    for s,d in pairs:
        patch_docx(s,d)
        print('wrote',d)
