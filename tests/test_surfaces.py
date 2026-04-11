"""Surface resolution tests — the cross-audience correctness proof.

If the same code resolves different surfaces for a Shopify tool vs a Claude Code
plugin vs an MCP server, the registry abstraction works. That's the whole point.
"""

from __future__ import annotations

from pathlib import Path

from pipeline.registry import Project, load
from pipeline.surfaces import Directory, ResolvedSurfaces, SurfaceRegistry

REPO_ROOT = Path(__file__).parent.parent


def _surfaces() -> SurfaceRegistry:
    return SurfaceRegistry.load(REPO_ROOT / "surfaces.yml")


def _project(audience: str, kind: str, name: str = "test") -> Project:
    return Project(
        repo="https://example.com/test",
        kind=kind,
        audience=audience,
        status="live",
        problem="p",
        solution_one_liner="s",
        facts=["one", "two"],
        angles=[],
        channels=["bluesky"],
    )


def test_mcp_server_resolves_to_mcp_directories() -> None:
    surfaces = _surfaces()
    resolved = surfaces.resolve(_project("mcp-users", "mcp-server"))
    names = [d.name for d in resolved.directories]
    assert "mcp-registry" in names
    assert "smithery" in names
    assert "pulsemcp" in names
    assert "awesome-mcp-servers" in names


def test_terminal_theme_resolves_to_theme_directories() -> None:
    surfaces = _surfaces()
    resolved = surfaces.resolve(_project("claude-code-users", "terminal-theme"))
    names = [d.name for d in resolved.directories]
    # audience directories
    assert "awesome-claude-code" in names
    # kind-additive directories
    assert "iterm2-color-schemes" in names
    assert "base16-schemes" in names
    assert "gogh" in names
    # sanity: r/unixporn in forums from kind
    assert "r_unixporn" in resolved.forums_manual


def test_chrome_extension_for_research_devs() -> None:
    surfaces = _surfaces()
    resolved = surfaces.resolve(_project("research-devs", "chrome-extension"))
    names = [d.name for d in resolved.directories]
    assert "chrome-web-store" in names
    assert "firefox-amo" in names
    assert "edge-addons" in names
    assert "awesome-webextensions" in names


def test_ecom_cli_audit_tool_has_different_surface_set() -> None:
    """The critical cross-audience test: a Shopify tool must NOT see MCP directories."""
    surfaces = _surfaces()
    resolved = surfaces.resolve(_project("ecom-solopreneurs", "cli-audit-tool"))
    names = [d.name for d in resolved.directories]
    # Ecom surfaces present
    assert "alternativeto" in names
    assert "uneed" in names
    assert "indiehackers-products" in names
    # MCP surfaces absent
    assert "mcp-registry" not in names
    assert "awesome-claude-code" not in names
    # Ecom forums present
    assert "r_ecommerce" in resolved.forums_manual
    assert "product_hunt" in resolved.forums_manual


def test_daily_channels_dedupes_across_social_and_blogs() -> None:
    surfaces = _surfaces()
    resolved = surfaces.resolve(_project("ecom-solopreneurs", "cli-audit-tool"))
    # bluesky from daily_social, devto from content_blogs, indiehackers listed in both
    channels = resolved.daily_channels
    # No duplicates
    assert len(channels) == len(set(channels))


def test_resolve_uses_real_projects() -> None:
    """End-to-end: load real projects.yml + resolve against surfaces.yml."""
    registry = load(REPO_ROOT / "projects.yml")
    surfaces = _surfaces()

    konid_resolved = surfaces.resolve(registry.get("konid"))
    assert len(konid_resolved.directories) >= 5  # at minimum the MCP cluster

    rabbitholes_resolved = surfaces.resolve(registry.get("rabbitholes"))
    rh_names = [d.name for d in rabbitholes_resolved.directories]
    assert "chrome-web-store" in rh_names

    # Same pipeline, different surface sets.
    konid_names = {d.name for d in konid_resolved.directories}
    rh_name_set = {d.name for d in rabbitholes_resolved.directories}
    assert konid_names != rh_name_set


def test_unknown_audience_raises() -> None:
    surfaces = _surfaces()
    p = Project(
        repo="https://example.com/x",
        kind="mcp-server",
        audience="nonexistent-audience",
        status="live",
        problem="p",
        solution_one_liner="s",
        facts=["one"],
        angles=[],
        channels=["bluesky"],
    )
    try:
        surfaces.resolve(p)
    except KeyError as e:
        assert "nonexistent-audience" in str(e)
    else:
        raise AssertionError("expected KeyError for unknown audience")


def test_directory_dataclass_accepts_all_types() -> None:
    """Sanity: Directory dataclass handles pr / cli / form / contact shapes."""
    d1 = Directory(name="foo", type="pr", repo="a/b")
    d2 = Directory(name="bar", type="cli", tool="cli-tool")
    d3 = Directory(name="baz", type="form", url="https://example.com/submit")
    d4 = Directory(name="qux", type="contact", contact="email foo@bar")
    assert d1.repo == "a/b"
    assert d2.tool == "cli-tool"
    assert d3.url == "https://example.com/submit"
    assert d4.contact == "email foo@bar"
