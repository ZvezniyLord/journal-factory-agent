from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import shape_object_fidelity as sof

class ShapeObjectFidelityTest(unittest.TestCase):
    def test_textbox_signature_detection(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'x.docx'
            xml=b'''<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:pict><w:txbxContent><w:p><w:r><w:t>Shape text</w:t></w:r></w:p></w:txbxContent></w:pict></w:r></w:p></w:body></w:document>'''
            with ZipFile(p,'w',ZIP_DEFLATED) as z: z.writestr('word/document.xml',xml)
            with ZipFile(p) as z:
                sig=sof.textbox_signatures(z)
            self.assertEqual(sig[0]['text'],'Shape text')

if __name__=='__main__': unittest.main()
