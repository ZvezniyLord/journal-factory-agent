import zipfile, tempfile, shutil, re
from pathlib import Path
from lxml import etree
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main';NS={'w':W};q=lambda x:f'{{{W}}}{x}'
SRC=Path('/mnt/data/JOURNAL_136_FULL_RELEASE_v31.docx'); OUT=Path('/mnt/data/JOURNAL_136_FULL_RELEASE_v31.docx')
def text(p):return re.sub(r'\s+',' ',''.join(p.xpath('.//w:t/text()',namespaces=NS))).strip()
def style(p):
 x=p.find('w:pPr/w:pStyle',NS);return x.get(q('val')) if x is not None else ''
def settext(p,s):
 for ch in list(p):
  if ch.tag!=q('pPr'):p.remove(ch)
 r=etree.SubElement(p,q('r'));rpr=etree.SubElement(r,q('rPr'));etree.SubElement(rpr,q('b'))
 f=etree.SubElement(rpr,q('rFonts'))
 for a in ('ascii','hAnsi','eastAsia','cs'):f.set(q(a),'Times New Roman')
 for tag in ('sz','szCs'):
  x=etree.SubElement(rpr,q(tag));x.set(q('val'),'22')
 t=etree.SubElement(r,q('t'));t.text=s
def heading_for(title,current):
 if re.search(r'literatur|quellen',current,re.I):return current
 cyr=sum(1 for c in title if c in 'АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯабвгґдеєжзиіїйклмнопрстуфхцчшщьюя')
 lat=sum(1 for c in title if 'A'<=c<='Z' or 'a'<=c<='z')
 return 'СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ:' if cyr>=lat else 'REFERENCES'
work=Path(tempfile.mkdtemp())
try:
 with zipfile.ZipFile(SRC) as z:z.extractall(work)
 p=work/'word/document.xml';root=etree.parse(str(p)).getroot();body=root.find('w:body',NS)
 current_title='';changes=[]
 for ch in body:
  if ch.tag!=q('p'):continue
  if style(ch)=='11':current_title=text(ch)
  if style(ch)=='REF-TITLE':
   old=text(ch);new=heading_for(current_title,old)
   if new!=old:settext(ch,new);changes.append((current_title,old,new))
 etree.ElementTree(root).write(str(p),encoding='UTF-8',xml_declaration=True,standalone=True)
 tmp=OUT.with_suffix('.tmp.docx')
 with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as z:
  for f in work.rglob('*'):
   if f.is_file():z.write(f,f.relative_to(work).as_posix())
 tmp.replace(OUT)
 print(changes)
finally:shutil.rmtree(work,ignore_errors=True)
