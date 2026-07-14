from pathlib import Path
import sys
from lxml import etree
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import finalize_business_semantics as fbs

def p(text, style=''):
    e=etree.Element(fbs.qn('p'))
    if style:
        ppr=etree.SubElement(e,fbs.qn('pPr')); ps=etree.SubElement(ppr,fbs.qn('pStyle')); ps.set(fbs.qn('val'),style)
    r=etree.SubElement(e,fbs.qn('r')); t=etree.SubElement(r,fbs.qn('t')); t.text=text
    return e

def test_manual_numbering_and_enter_continuation_are_reconstructed():
    body=etree.Element(fbs.qn('body'))
    a=p('1. Автор А. Назва праці.'); cont=p('Продовження після випадкового Enter.'); b=p('2) Автор Б. DOI https://doi.org/10.1234/test')
    body.extend([a,cont,b])
    entries=fbs.reconstruct_reference_entries(body,list(body))
    assert len(entries)==2 and len(body)==2
    assert 'Продовження після випадкового Enter.' in fbs.paragraph_text(entries[0])
    assert fbs.ensure_label_before_urls(fbs.paragraph_text(entries[1])).endswith('DOI: https://doi.org/10.1234/test')

def test_url_and_doi_labels():
    t=fbs.ensure_label_before_urls('Site https://example.com. Paper 10.5555/ABC. URL: https://doi.org/10.7777/z')
    assert 'URL: https://example.com' in t
    assert 'DOI: 10.5555/ABC' in t
    assert 'DOI: https://doi.org/10.7777/z' in t
    assert 'URL: https://doi.org' not in t

def test_ambiguous_unnumbered_multiline_list_stops():
    body=etree.Element(fbs.qn('body')); body.extend([p('Author A source'),p('Author B source')])
    with pytest.raises(RuntimeError,match='REFERENCE_BOUNDARIES_AMBIGUOUS'):
        fbs.reconstruct_reference_entries(body,list(body))
