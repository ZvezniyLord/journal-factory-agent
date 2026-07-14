from __future__ import annotations
import argparse, json, posixpath, re
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree

PKG_REL='http://schemas.openxmlformats.org/package/2006/relationships'
OFF_REL='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
DGM='http://schemas.openxmlformats.org/drawingml/2006/diagram'
A='http://schemas.openxmlformats.org/drawingml/2006/main'
DSP='http://schemas.microsoft.com/office/drawing/2008/diagram'
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
WP='http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'
CT='http://schemas.openxmlformats.org/package/2006/content-types'
DIAGRAM_DRAWING_TYPE='http://schemas.microsoft.com/office/2007/relationships/diagramDrawing'
DIAGRAM_DRAWING_CT='application/vnd.ms-office.drawingml.diagramDrawing+xml'
NS={'pr':PKG_REL,'r':OFF_REL,'dgm':DGM,'a':A,'dsp':DSP,'w':W,'wp':WP,'ct':CT}
R=lambda local:f'{{{OFF_REL}}}{local}'

def norm_part(base_part:str,target:str)->str:
    return posixpath.normpath(posixpath.join(posixpath.dirname(base_part),target))

def rels_name(part:str)->str:
    return posixpath.join(posixpath.dirname(part),'_rels',posixpath.basename(part)+'.rels')

def read_xml(z:ZipFile,name:str): return etree.fromstring(z.read(name))

def rel_map(z:ZipFile,part='word/document.xml'):
    rn=rels_name(part); root=read_xml(z,rn)
    return root,{x.get('Id'):x for x in root.xpath('.//pr:Relationship',namespaces=NS)}

def diagram_records(z:ZipFile):
    doc=read_xml(z,'word/document.xml')
    relroot,rels=rel_map(z)
    out=[]
    for idx,el in enumerate(doc.xpath('.//dgm:relIds',namespaces=NS),1):
        dm=el.get(R('dm'))
        dmrel=rels.get(dm)
        if dmrel is None: continue
        data_part=norm_part('word/document.xml',dmrel.get('Target'))
        data=read_xml(z,data_part)
        texts=[t.strip() for t in data.xpath('.//a:t/text()',namespaces=NS) if t.strip()]
        sig=' | '.join(texts)
        ext=el.xpath('ancestor::wp:inline[1]/wp:extent',namespaces=NS)
        extent=None if not ext else {'cx':ext[0].get('cx'),'cy':ext[0].get('cy')}
        dmx=data.xpath('.//dsp:dataModelExt',namespaces=NS)
        drawing_rid=dmx[0].get('relId') if dmx else None
        drawing_rel=rels.get(drawing_rid) if drawing_rid else None
        drawing_part=None
        valid=False
        if drawing_rel is not None and drawing_rel.get('Type')==DIAGRAM_DRAWING_TYPE:
            drawing_part=norm_part('word/document.xml',drawing_rel.get('Target'))
            valid=drawing_part in z.namelist()
        out.append({'index':idx,'dm_rid':dm,'data_part':data_part,'signature':sig,'text':texts,
                    'extent':extent,'drawing_rid':drawing_rid,'drawing_part':drawing_part,'drawing_valid':valid})
    return out

def textbox_signatures(z:ZipFile):
    vals=[]
    for n in z.namelist():
        if not (n.startswith('word/') and n.endswith('.xml')): continue
        try: root=read_xml(z,n)
        except Exception: continue
        for tx in root.xpath('.//w:txbxContent',namespaces=NS):
            txt=' '.join(t.strip() for t in tx.xpath('.//w:t/text()',namespaces=NS) if t.strip())
            if txt: vals.append({'part':n,'text':txt})
    return vals

def next_rid(relroot):
    nums=[]
    for x in relroot.xpath('.//pr:Relationship',namespaces=NS):
        m=re.fullmatch(r'rId(\d+)',x.get('Id',''))
        if m: nums.append(int(m.group(1)))
    return f'rId{max(nums,default=0)+1}'

def unique_drawing_name(existing):
    i=1
    while f'word/diagrams/drawing{i}.xml' in existing: i+=1
    return f'word/diagrams/drawing{i}.xml'

def audit(source:Path,target:Path):
    with ZipFile(source) as zs, ZipFile(target) as zt:
        sr=diagram_records(zs); tr=diagram_records(zt)
        issues=[]
        unused=list(tr)
        matched=[]
        for i,s in enumerate(sr,1):
            t=next((x for x in unused if x['signature']==s['signature']),None)
            if t is None:
                issues.append({'kind':'missing_smartart','index':i,'signature':s['signature']})
                continue
            unused.remove(t); matched.append((s,t))
            if s['extent']!=t['extent']: issues.append({'kind':'smartart_extent','index':i,'source':s['extent'],'target':t['extent']})
            if not t['drawing_valid']: issues.append({'kind':'missing_diagram_drawing','index':i,'target_rel':t['drawing_rid']})
            if t['drawing_valid'] and s['drawing_valid']:
                if zs.read(s['drawing_part'])!=zt.read(t['drawing_part']): issues.append({'kind':'diagram_drawing_xml_diff','index':i})
        st=textbox_signatures(zs); tt=textbox_signatures(zt)
        remaining=[x['text'] for x in tt]
        missing=[]
        for x in st:
            if x['text'] in remaining:
                remaining.remove(x['text'])
            else:
                missing.append(x['text'])
        if missing:
            issues.append({'kind':'missing_textbox_text','missing':missing,'source_count':len(st),'target_count':len(tt)})
        return {'source':str(source),'target':str(target),'source_diagrams':sr,'target_diagrams':tr,
                'source_textboxes':st,'target_textboxes':tt,'issues':issues,'status':'pass' if not issues else 'fail'}

def repair(source:Path,target:Path,output:Path):
    with ZipFile(source) as zs, ZipFile(target) as zt:
        source_records=diagram_records(zs); target_records=diagram_records(zt)
        files={n:zt.read(n) for n in zt.namelist()}
        existing=set(files)
        rel_name=rels_name('word/document.xml')
        relroot=etree.fromstring(files[rel_name])
        _, target_relmap=rel_map(zt)
        ctroot=etree.fromstring(files['[Content_Types].xml'])
        fixes=[]
        # pair by exact text signature, fallback by order
        unused=list(source_records)
        for t in target_records:
            if t['drawing_valid']: continue
            s=next((x for x in unused if x['signature']==t['signature'] and x['drawing_valid']),None)
            if s is None and unused:
                s=next((x for x in unused if x['drawing_valid']),None)
            if s is None: continue
            unused.remove(s)
            src_draw=s['drawing_part']
            src_rels=rels_name(src_draw)
            if src_rels in zs.namelist():
                raise RuntimeError(f'Diagram drawing has dependent relationships ({src_rels}); operator review required')
            new_part=unique_drawing_name(existing)
            existing.add(new_part); files[new_part]=zs.read(src_draw)
            rid=next_rid(relroot)
            rel=etree.SubElement(relroot,f'{{{PKG_REL}}}Relationship')
            rel.set('Id',rid); rel.set('Type',DIAGRAM_DRAWING_TYPE)
            rel.set('Target',posixpath.relpath(new_part,posixpath.dirname('word/document.xml')))
            # patch target data model extension
            data_root=etree.fromstring(files[t['data_part']])
            exts=data_root.xpath('.//dsp:dataModelExt',namespaces=NS)
            if not exts:
                raise RuntimeError(f'No dataModelExt in {t["data_part"]}')
            old=exts[0].get('relId'); exts[0].set('relId',rid)
            files[t['data_part']]=etree.tostring(data_root,xml_declaration=True,encoding='UTF-8')
            # add content type
            part_name='/'+new_part
            has=ctroot.xpath(f'.//ct:Override[@PartName="{part_name}"]',namespaces=NS)
            if not has:
                ov=etree.SubElement(ctroot,f'{{{CT}}}Override')
                ov.set('PartName',part_name); ov.set('ContentType',DIAGRAM_DRAWING_CT)
            fixes.append({'diagram_index':t['index'],'signature':t['signature'],'old_relId':old,
                          'new_relId':rid,'copied_part':new_part})
        files[rel_name]=etree.tostring(relroot,xml_declaration=True,encoding='UTF-8')
        files['[Content_Types].xml']=etree.tostring(ctroot,xml_declaration=True,encoding='UTF-8')
        with ZipFile(output,'w',ZIP_DEFLATED) as zo:
            for n,d in files.items(): zo.writestr(n,d)
    report=audit(source,output); report['fixes']=fixes; return report

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('source',type=Path); ap.add_argument('target',type=Path)
    ap.add_argument('--output',type=Path); ap.add_argument('--audit-json',type=Path,required=True)
    a=ap.parse_args()
    report=repair(a.source,a.target,a.output) if a.output else audit(a.source,a.target)
    a.audit_json.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':report['status'],'issue_count':len(report['issues']),'fixes':len(report.get('fixes',[]))},ensure_ascii=False))
if __name__=='__main__': main()
