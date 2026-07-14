from pathlib import Path
import tempfile, zipfile, sys
from lxml import etree
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import finalize_business_semantics as fbs

def c14n(e): return etree.tostring(e,method='c14n')

def test_patch_copies_exact_canonical_nodes_from_jurnal_dotx():
    template=ROOT/'tests'/'fixtures'/'Jurnal.dotx'
    with tempfile.TemporaryDirectory() as td:
        td=Path(td)
        with zipfile.ZipFile(template) as z:
            z.extract('word/styles.xml',td/'src')
            z.extract('word/styles.xml',td/'tgt')
        # Deliberately alter SECTION in target.
        path=td/'tgt'/'word'/'styles.xml'; tree=etree.parse(str(path))
        sec=tree.xpath('//w:style[@w:styleId="SECTION"]',namespaces=fbs.NS)[0]
        sec.find('w:rPr/w:sz',fbs.NS).set(fbs.qn('val'),'22')
        tree.write(str(path),xml_declaration=True,encoding='UTF-8',standalone='yes')
        fbs.patch_styles(path,td/'src'/'word'/'styles.xml')
        out=etree.parse(str(path)); src=etree.parse(str(td/'src'/'word'/'styles.xml'))
        for sid in ['SECTION','11','AUTOR','pip','UDC','TABLETEXT','REF-TITLE','REFER']:
            a=out.xpath(f'//w:style[@w:styleId="{sid}"]',namespaces=fbs.NS)[0]
            b=src.xpath(f'//w:style[@w:styleId="{sid}"]',namespaces=fbs.NS)[0]
            assert c14n(a)==c14n(b)
