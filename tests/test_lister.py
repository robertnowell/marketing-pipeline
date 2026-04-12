"""Lister tests — directory submission plan generation."""

from __future__ import annotations

from pipeline.lister import plan_listings
from pipeline.registry import Project


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
        kind="claude-skill",
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


def test_mcp_server_gets_all_mcp_directories() -> None:
    plan = plan_listings(_mcp_project(), "konid")
    dirs = [s.directory for s in plan.submissions]
    assert "Official MCP Registry" in dirs
    assert "Smithery" in dirs
    assert "mcp.so" in dirs
    assert "mcpservers.org" in dirs
    assert "PulseMCP" in dirs
    assert "Glama" in dirs
    assert "awesome-claude-code" in dirs
    assert "GitHub Topics (SkillsMP auto-index)" in dirs


def test_mcp_server_automated_submissions() -> None:
    plan = plan_listings(_mcp_project(), "konid")
    auto = plan.automated
    auto_dirs = [s.directory for s in auto]
    assert "Official MCP Registry" in auto_dirs
    assert "Smithery" in auto_dirs
    assert "GitHub Topics (SkillsMP auto-index)" in auto_dirs
    # These should NOT be automated
    manual_dirs = [s.directory for s in plan.manual]
    assert "mcpservers.org" in manual_dirs
    assert "PulseMCP" in manual_dirs


def test_mcp_publisher_command() -> None:
    plan = plan_listings(_mcp_project(), "konid")
    registry_sub = next(s for s in plan.submissions if s.directory == "Official MCP Registry")
    assert registry_sub.command == "mcp-publisher publish"
    assert registry_sub.automated is True


def test_smithery_command_includes_repo_url() -> None:
    plan = plan_listings(_mcp_project(), "konid")
    smithery_sub = next(s for s in plan.submissions if s.directory == "Smithery")
    assert "robertnowell/konid" in smithery_sub.command
    assert smithery_sub.automated is True


def test_github_topics_for_mcp_server() -> None:
    plan = plan_listings(_mcp_project(), "konid")
    topics_sub = next(
        s for s in plan.submissions if s.directory == "GitHub Topics (SkillsMP auto-index)"
    )
    assert "mcp" in topics_sub.command
    assert "mcp-server" in topics_sub.command


def test_skill_project_gets_claude_marketplace() -> None:
    plan = plan_listings(_skill_project(), "skill-tree")
    dirs = [s.directory for s in plan.submissions]
    assert "Claude Plugin Marketplace" in dirs
    assert "awesome-claude-code" in dirs
    # Should NOT get MCP-specific directories
    assert "Official MCP Registry" not in dirs
    assert "Smithery" not in dirs


def test_skill_project_github_topics() -> None:
    plan = plan_listings(_skill_project(), "skill-tree")
    topics_sub = next(
        s for s in plan.submissions if s.directory == "GitHub Topics (SkillsMP auto-index)"
    )
    assert "claude-skill" in topics_sub.command
    assert "claude-code" in topics_sub.command


def test_extension_project_no_mcp_directories() -> None:
    plan = plan_listings(_extension_project(), "rabbitholes")
    dirs = [s.directory for s in plan.submissions]
    assert "Official MCP Registry" not in dirs
    assert "Smithery" not in dirs
    assert "Claude Plugin Marketplace" not in dirs


def test_awesome_claude_code_pr_body() -> None:
    plan = plan_listings(_mcp_project(), "konid")
    pr_sub = next(s for s in plan.submissions if s.directory == "awesome-claude-code")
    assert pr_sub.pr_body is not None
    assert "konid" in pr_sub.pr_body
    assert "robertnowell/konid" in pr_sub.pr_body


def test_listing_plan_repo_url() -> None:
    plan = plan_listings(_mcp_project(), "konid")
    assert plan.repo_url == "https://github.com/robertnowell/konid"
