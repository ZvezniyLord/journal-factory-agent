from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import udc_lookup_request as ulr

def test_missing_udc_creates_online_review_packet():
    req=ulr.build_request(ROOT/'tests'/'fixtures'/'header_contact_standalone_email.docx','a-1','PSYCHOLOGY AND PSYCHIATRY')
    assert req['status']=='UDC_LOOKUP_REQUIRED'
    assert req['needs_operator_review'] is True
    assert req['title']
    assert 'online' in req['instruction'].lower()

def test_udc_skill_requires_exact_one_blank_and_approval():
    text=(ROOT/'skills'/'naukainfo-udc-review'/'MODULE.md').read_text(encoding='utf-8')
    assert 'exactly one empty Normal paragraph after the UDC' in text
    assert 'operator approval' in text
    assert 'online-capable' in text
