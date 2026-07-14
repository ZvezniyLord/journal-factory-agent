from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "mcp_server"))
import core


class SafetyTest(unittest.TestCase):
    def test_output_cannot_be_inside_raw_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "raw"
            raw.mkdir()
            template = Path(tmp) / "template.docx"
            template.write_bytes(b"x")
            with self.assertRaises(ValueError):
                core._assert_output_isolated(raw, template, raw / "out")

    def test_build_requires_confirmation(self):
        with self.assertRaises(PermissionError):
            core.build_journal(".", "raw", "template.docx", "out", "NO")


if __name__ == "__main__":
    unittest.main()
