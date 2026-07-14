from __future__ import annotations

from mcp.server.fastmcp import FastMCP

import core

mcp = FastMCP("NAUKAINFO Journal Builder")


@mcp.tool()
def read_project_context(project_root: str = ""):
    """Read architecture and project memory before planning or changing the Journal Builder."""
    return core.read_project_context(project_root or None)


@mcp.tool()
def run_unit_tests(project_root: str = "", timeout: int = 600):
    """Run the current unittest suite without changing project files."""
    return core.run_unit_tests(project_root or None, timeout)


@mcp.tool()
def snapshot_inputs(path: str):
    """Create SHA-256 snapshot of a file or directory for immutability checks."""
    return core.snapshot_tree(path)


@mcp.tool()
def test_llm_endpoint(project_root: str, workspace: str, base_url: str, model: str, timeout_seconds: int = 300):
    """Run the existing non-DOCX LLM smoke test."""
    return core.test_llm_endpoint(project_root or None, workspace, base_url, model, timeout_seconds)


@mcp.tool()
def template_snapshot(project_root: str, template: str, output: str):
    """Read template styles and write a snapshot without modifying the template."""
    return core.template_snapshot(project_root or None, template, output)


@mcp.tool()
def scan_conference(project_root: str, raw_root: str, template: str, workspace: str, llm_base_url: str = "", llm_model: str = "", enable_internal_llm: bool = False, timeout_seconds: int = 300):
    """Run safe scan-only conference intake. Internal LLM is off unless explicitly enabled."""
    return core.scan_conference(project_root or None, raw_root, template, workspace, llm_base_url, llm_model, enable_internal_llm, timeout_seconds)


@mcp.tool()
def read_scan_reports(workspace: str):
    """Read JSON reports created by scan-conference."""
    return core.read_scan_reports(workspace)


@mcp.tool()
def inspect_docx_readonly(path: str, max_paragraphs: int = 80):
    """Inspect DOCX front matter, table cells and object counts without saving the document."""
    return core.inspect_docx_readonly(path, max_paragraphs)


@mcp.tool()
def build_journal(project_root: str, raw_root: str, template: str, output_root: str, approval: str, llm_base_url: str = "", llm_model: str = "", enable_internal_llm: bool = False, enable_internal_manifest_llm: bool = False, timeout_seconds: int = 300):
    """Run full prepare-conference on isolated outputs. Requires approval='BUILD_CONFIRMED'."""
    return core.build_journal(project_root or None, raw_root, template, output_root, approval, llm_base_url, llm_model, enable_internal_llm, enable_internal_manifest_llm, timeout_seconds)


@mcp.tool()
def list_run_artifacts(run_dir: str):
    """List files produced by a run."""
    return core.list_run_artifacts(run_dir)


@mcp.tool()
def audit_docx(project_root: str, docx: str, out_dir: str):
    """Run the existing DOCX audits on a built copy."""
    return core.audit_docx(project_root or None, docx, out_dir)


@mcp.tool()
def quality_gate(project_root: str, audit_dir: str, output: str, operator_actions: str):
    """Run deterministic final quality gate; LLM cannot override it."""
    return core.quality_gate(project_root or None, audit_dir, output, operator_actions)


@mcp.tool()
def render_docx_pdf(docx: str, output_pdf: str):
    """Render a DOCX copy to PDF through Microsoft Word in read-only mode."""
    return core.render_docx_pdf(docx, output_pdf)


if __name__ == "__main__":
    mcp.run()
