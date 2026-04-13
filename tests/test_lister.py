"""Lister tests — data-driven directory submission from surfaces.yml."""

from __future__ import annotations

from pathlib import Path

from pipeline.lister import plan_listings
from pipeline.registry import Project

REPO_ROOT = Path(__file__).parent.parent


def _mcp_project() -> Project:
    return Project(
        repo="robertnowell/konid",
        kind="mcp-server",
        audience="mcp-users",
        status="live",
        problem="Google Translate gives one literal translation with no register context.",
        solution_one_liner="Returns three expression options casual-to-formal with pronunciation.",
        facts=["13+ languages", "works in Claude Code, Cursor, and Claude Desktop"],
        angles=[],
    )


def _skill_project() -> Project:
    return Project(
        repo="robertnowell/skill-tree",
        kind="claude-code-plugin",
        audience="claude-code-users",
        status="live",
        problem="No way to see your collaboration style with Claude Code.",
        solution_one_liner="Analyzes your sessions and generates a skill tree visualization.",
        facts=[],
        angles=[],
    )


def _extension_project() -> Project:
    return Project(
        repo="robertnowell/rabbitholes",
        kind="browser-extension",
        audience="knowledge-workers",
        status="live",
        problem="Tab-switching kills web research flow.",
        solution_one_liner="Inline explanations next to your cursor, click any word to dig deeper.",
        facts=[],
        angles=[],
    )


def _multi_kind_project() -> Project:
    """A project that is both an MCP server and a Claude skill."""
    return Project(
        repo="robertnowell/konid",
        kind="mcp-server,claude-code-plugin",
        audience="mcp-users",
        status="live",
        problem="Translation tools give one answer with no context.",
        solution_one_liner="Three options casual to formal with pronunciation.",
        facts=[],
        angles=[],
    )


def test_mcp_server_gets_mcp_directories() -> None:
    plan = plan_listings(_mcp_project(), "konid", REPO_ROOT / "surfaces.yml")
    dirs = [s.directory for s in plan.submissions]
    assert "mcp-registry" in dirs
    assert "smithery" in dirs
    assert "pulsemcp" in dirs


def test_mcp_server_has_automated_submissions() -> None:
    plan = plan_listings(_mcp_project(), "konid", REPO_ROOT / "surfaces.yml")
    auto_dirs = [s.directory for s in plan.automated]
    assert "GitHub Topics" in auto_dirs
    assert "mcp-registry" in auto_dirs or any("mcp" in d for d in auto_dirs)


def test_skill_project_gets_claude_directories() -> None:
    plan = plan_listings(_skill_project(), "skill-tree", REPO_ROOT / "surfaces.yml")
    dirs = [s.directory for s in plan.submissions]
    assert "awesome-claude-code" in dirs


def test_extension_project_gets_browser_directories() -> None:
    plan = plan_listings(_extension_project(), "rabbitholes", REPO_ROOT / "surfaces.yml")
    dirs = [s.directory for s in plan.submissions]
    assert "chrome-web-store" in dirs
    assert "firefox-amo" in dirs
    assert "edge-addons" in dirs


def test_extension_project_no_mcp_directories() -> None:
    plan = plan_listings(_extension_project(), "rabbitholes", REPO_ROOT / "surfaces.yml")
    dirs = [s.directory for s in plan.submissions]
    assert "mcp-registry" not in dirs
    assert "smithery" not in dirs


def test_claude_code_users_get_devhunt() -> None:
    """claude-code-users audience includes DevHunt and Uneed."""
    plan = plan_listings(_skill_project(), "skill-tree", REPO_ROOT / "surfaces.yml")
    dirs = [s.directory for s in plan.submissions]
    assert "devhunt" in dirs
    assert "uneed" in dirs


def test_multi_kind_gets_both_directory_sets() -> None:
    """A project with kind 'mcp-server,claude-code-plugin' gets both MCP and Claude dirs."""
    plan = plan_listings(_multi_kind_project(), "konid", REPO_ROOT / "surfaces.yml")
    dirs = [s.directory for s in plan.submissions]
    # MCP directories
    assert "mcp-registry" in dirs
    assert "smithery" in dirs
    # Claude directories
    assert "awesome-claude-code" in dirs


def test_listing_plan_repo_url() -> None:
    plan = plan_listings(_mcp_project(), "konid", REPO_ROOT / "surfaces.yml")
    assert plan.repo_url == "https://github.com/robertnowell/konid"


def test_pr_submissions_have_body() -> None:
    plan = plan_listings(_mcp_project(), "konid", REPO_ROOT / "surfaces.yml")
    pr_subs = [s for s in plan.submissions if s.method == "pr"]
    for s in pr_subs:
        assert s.pr_body is not None, f"{s.directory} missing PR body"
        assert "konid" in s.pr_body
