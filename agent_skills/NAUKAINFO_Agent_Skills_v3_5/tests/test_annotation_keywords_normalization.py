from pathlib import Path
import sys
from lxml import etree
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import finalize_business_semantics as fbs

def make_p(text):
    p=etree.Element(fbs.qn('p')); r=etree.SubElement(p,fbs.qn('r')); t=etree.SubElement(r,fbs.qn('t')); t.text=text; return p

def run_texts(p):
    return [(r.find(fbs.qn('t')).text or '', r.find(fbs.qn('rPr')) is not None and r.find(fbs.qn('rPr')).find(fbs.qn('b')) is not None) for r in p.findall(fbs.qn('r'))]

def test_ukrainian_annotation_and_keywords():
    a=make_p('Анотація: у статті досліджено тему.')
    k=make_p('КЛЮЧОВІ СЛОВА. Мотивація, HR, AI.')
    assert fbs.canonicalize_annotation_or_keywords(a)
    assert fbs.canonicalize_annotation_or_keywords(k)
    assert fbs.get_pstyle(a)=='a0' and fbs.get_pstyle(k)=='a0'
    ar=run_texts(a); kr=run_texts(k)
    assert ar[0]==('Анотація.',True) and ar[1][0].startswith(' У статті') and not ar[1][1]
    assert kr[0]==('Ключові слова:',True) and kr[1][0].startswith(' мотивація')

def test_english_abstract_and_acronym_keyword():
    a=make_p('ABSTRACTS. this study analyses data.')
    k=make_p('KEYWORDS. AI, machine learning.')
    fbs.canonicalize_annotation_or_keywords(a); fbs.canonicalize_annotation_or_keywords(k)
    assert run_texts(a)[1][0].startswith(' This study')
    assert run_texts(k)[1][0].startswith(' AI')
