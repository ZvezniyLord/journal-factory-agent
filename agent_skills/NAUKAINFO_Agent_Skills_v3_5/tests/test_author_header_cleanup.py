from pathlib import Path
import sys
from docx import Document
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import finalize_business_semantics as fbs
FIX=ROOT/'tests'/'fixtures'

def cleaned_texts(path):
    result=[]
    for p in Document(path).paragraphs:
        t=p.text.strip()
        if not t: continue
        c=fbs.strip_contact_data(t)
        if c: result.append(c)
    return result

def test_standalone_email_removed_without_losing_header():
    texts=cleaned_texts(FIX/'header_contact_standalone_email.docx')
    assert not any('@' in t for t in texts)
    assert 'Шевчук Віта Станіславівна' in texts
    assert any(t.startswith('студентка') for t in texts)

def test_two_emails_removed_and_orcid_preserved():
    texts=cleaned_texts(FIX/'header_contacts_orcid_english.docx')
    assert not any('@' in t for t in texts)
    assert any('orcid.org/0009-0004-4971-3340' in t for t in texts)
    assert 'Sherbon Fedir' in texts and 'Sherbon Olena' in texts

def test_role_case_normalization():
    assert fbs.normalize_role_case('Студентка спеціальності психологія')=='студентка спеціальності психологія'
    assert fbs.normalize_role_case('Кандидат наук, Доцент')=='кандидат наук, Доцент'
