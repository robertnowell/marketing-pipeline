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


def test_chrome_extension_for_knowledge_workers() -> None:
    surfaces = _surfaces()
    resolved = surfaces.resolve(_project("knowledge-workers", "chrome-extension"))
    names = [d.name for d in resolved.directories]
    assert "chrome-web-store" in names
    assert "firefox-amo" in names
    assert "edge-addons" in names
    assert "awesome-webextensions" in names


def test_browser_extension_kind_works_across_audiences() -> None:
    """The `browser-extension` kind uses full dict entries (not string refs),
    so it should resolve its three stores regardless of what audience the
    project is in. This is the proof that kinds aren't implicitly coupled
    to the audience that first defined a directory.
    """
    surfaces = _surfaces()
    # A consumer-audience browser extension (e.g. a general-public tab manager)
    resolved = surfaces.resolve(_project("general-consumers", "browser-extension"))
    names = [d.name for d in resolved.directories]
    assert "chrome-web-store" in names
    assert "firefox-amo" in names
    assert "edge-addons" in names
    # And still picks up the audience's own directories
    assert "product-hunt-launch" in names


def test_consumer_web_app_resolves_to_consumer_surfaces() -> None:
    """The critical non-dev cross-audience test. A consumer web app must
    resolve to consumer-facing directories (Product Hunt, TAAFT, AlternativeTo)
    and forums (r_apps, instagram_manual, tiktok_manual) — and must NOT see
    dev-tool directories (mcp-registry, awesome-claude-code, iterm2-color-schemes).
    If this passes, the audience/kind abstraction is actually project-agnostic.
    """
    surfaces = _surfaces()
    resolved = surfaces.resolve(_project("general-consumers", "consumer-web-app"))
    names = [d.name for d in resolved.directories]
    # Consumer surfaces present
    assert "product-hunt-launch" in names
    assert "taaft" in names
    assert "alternativeto" in names
    assert "futuretools" in names
    # Dev-tool surfaces absent
    assert "mcp-registry" not in names
    assert "awesome-claude-code" not in names
    assert "iterm2-color-schemes" not in names
    assert "awesome-webextensions" not in names
    # Consumer forums present
    assert "instagram_manual" in resolved.forums_manual
    assert "tiktok_manual" in resolved.forums_manual
    assert "r_apps" in resolved.forums_manual


def test_founders_b2b_saas_resolves_correctly() -> None:
    """A B2B SaaS for founders/solopreneurs should see IndieHackers, HN, and
    the B2B review directories — not Claude Code lists, not MCP registries."""
    surfaces = _surfaces()
    resolved = surfaces.resolve(_project("founders-solopreneurs", "b2b-saas"))
    names = [d.name for d in resolved.directories]
    # Founder surfaces
    assert "indiehackers-products" in names
    assert "product-hunt-launch" in names
    # B2B-saas kind adds
    assert "g2" in names
    assert "capterra" in names
    # Dev-tool absent
    assert "mcp-registry" not in names
    assert "awesome-claude-code" not in names
    # Founder forums
    assert "indiehackers_main" in resolved.forums_manual
    assert "hn_show" in resolved.forums_manual
    assert "linkedin_manual" in resolved.forums_manual


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


def test_watering_holes_resolved_for_live_audiences() -> None:
    """The three audiences with live projects (claude-code-users, mcp-users,
    knowledge-workers) should each resolve to a non-empty watering-hole list,
    with type discriminators the safari.py dispatcher will understand.
    Audiences without watering_holes populated must default to an empty list
    (not raise) so the schema is forward-compatible.
    """
    surfaces = _surfaces()

    # claude-code-users has watering holes
    cc = surfaces.resolve(_project("claude-code-users", "claude-code-plugin"))
    assert len(cc.watering_holes) > 0
    cc_types = {wh["type"] for wh in cc.watering_holes}
    assert "hn_algolia" in cc_types
    assert "reddit_search" in cc_types
    assert "bluesky_search" in cc_types
    # Spot-check one entry's fields
    reddit_entries = [wh for wh in cc.watering_holes if wh["type"] == "reddit_search"]
    assert any(wh.get("sub") == "ClaudeAI" for wh in reddit_entries)

    # mcp-users has watering holes including GitHub Issues for the MCP repos
    mcp = surfaces.resolve(_project("mcp-users", "mcp-server"))
    assert len(mcp.watering_holes) > 0
    mcp_types = {wh["type"] for wh in mcp.watering_holes}
    assert "github_issues" in mcp_types
    gh_entries = [wh for wh in mcp.watering_holes if wh["type"] == "github_issues"]
    assert any("modelcontextprotocol/servers" in wh.get("repos", []) for wh in gh_entries)

    # knowledge-workers has watering holes targeting research pain, not dev tooling
    kw = surfaces.resolve(_project("knowledge-workers", "chrome-extension"))
    assert len(kw.watering_holes) > 0
    kw_keywords_flat = [
        k for wh in kw.watering_holes
        if wh["type"] == "bluesky_search"
        for k in wh.get("keywords", [])
    ]
    assert any("tab" in k or "rabbit" in k for k in kw_keywords_flat), (
        "knowledge-workers watering holes should target research/tab-management pain"
    )

    # An audience without watering_holes configured must default to empty list
    gc = surfaces.resolve(_project("general-consumers", "consumer-web-app"))
    assert gc.watering_holes == []

    # frontend-engineers is live-project-adjacent but not populated yet — empty
    fe = surfaces.resolve(_project("frontend-engineers", "saas-web-app"))
    assert fe.watering_holes == []


def test_watering_holes_not_cross_contaminated_by_audience() -> None:
    """Regression guard: mcp-users and knowledge-workers must NOT see each other's
    watering holes. The resolver's audience-only lookup for watering_holes
    (no kind-layering) is what makes per-project pain catalogs non-overlapping.
    """
    surfaces = _surfaces()
    mcp = surfaces.resolve(_project("mcp-users", "mcp-server"))
    kw = surfaces.resolve(_project("knowledge-workers", "chrome-extension"))

    mcp_reddit_subs = {wh.get("sub") for wh in mcp.watering_holes if wh["type"] == "reddit_search"}
    kw_reddit_subs = {wh.get("sub") for wh in kw.watering_holes if wh["type"] == "reddit_search"}

    # Each audience has its own distinct subreddit set
    assert "LocalLLaMA" in mcp_reddit_subs
    assert "LocalLLaMA" not in kw_reddit_subs
    assert "ObsidianMD" in kw_reddit_subs
    assert "ObsidianMD" not in mcp_reddit_subs


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
