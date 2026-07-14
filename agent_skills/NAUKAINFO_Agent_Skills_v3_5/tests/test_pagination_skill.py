from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PaginationSkillTest(unittest.TestCase):
    def test_pagination_break_skill_rules(self):
        text = (ROOT / "skills" / "naukainfo-pagination-break-reflow" / "MODULE.md").read_text(encoding="utf-8")
        self.assertIn("60/40", text)
        self.assertIn("article-start", text)
        self.assertIn("needs_operator_review", text)
        self.assertIn("render", text.lower())

    def test_add_to_skills_is_hard_command(self):
        text = (ROOT / "AGENT.md").read_text(encoding="utf-8")
        self.assertIn("додай до скілів", text)
        self.assertIn("новий архів", text)


if __name__ == "__main__":
    unittest.main()
