from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=spec_from_file_location('markers',ROOT/'scripts'/'normalize_multilingual_markers.py')
m=module_from_spec(spec); spec.loader.exec_module(m)

def test_reference_markers_multilingual():
    assert m.classify_reference_heading('14. Список використаних джерел') == ('uk','СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ:')
    assert m.classify_reference_heading('REFERENCE.') == ('en','REFERENCES')
    assert m.classify_reference_heading('Literaturverzeichnis') == ('de','LITERATURVERZEICHNIS:')
    assert m.classify_reference_heading('Quellenverzeichnis:') == ('de','QUELLENVERZEICHNIS:')

def test_figure_caption_markers():
    for text in ['Рис. 1. Схема','Fig. 2. Result','Abb. 4 Tinguely Museum','AGD1 Architecture']:
        assert m.is_figure_caption(text)

def test_unnumbered_table_marker():
    assert m.is_table_label('Таблиця')
    assert m.is_table_label('Tabelle')
    assert m.split_table_label_title('Таблиця 1 – Порівняння підходів') == ('Таблиця 1','Порівняння підходів')
