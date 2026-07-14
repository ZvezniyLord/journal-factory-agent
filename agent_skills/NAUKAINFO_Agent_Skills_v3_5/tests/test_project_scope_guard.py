from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_project_scope_guard_documented():
    text = (ROOT / "docs" / "PROJECT_SCOPE.md").read_text(encoding="utf-8")
    assert "Дирежор" in text
    assert "NAUKAINFO Journal Builder" in text
    assert "Заборонено" in text


def test_scope_in_agent_and_readme():
    agent = (ROOT / "AGENT.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Project scope" in agent
    assert "Project scope" in readme
    assert "unrelated chats" in agent
