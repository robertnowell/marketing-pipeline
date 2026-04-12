"""Registry load + validation tests."""

from __future__ import annotations

from pathlib import Path

from pipeline.registry import Project, Registry, load

REPO_ROOT = Path(__file__).parent.parent


def test_load_projects_yml() -> None:
    registry = load(REPO_ROOT / "projects.yml")
    assert isinstance(registry, Registry)
    assert "konid" in registry.projects
    assert "rabbitholes" in registry.projects


def test_live_projects_filters_wip() -> None:
    registry = load(REPO_ROOT / "projects.yml")
    live = registry.live_projects()
    # konid, rabbitholes, klein-blue, skill-tree are live; shopify-conjure is the wip placeholder.
    assert "konid" in live
    assert "rabbitholes" in live
    assert "klein-blue" in live
    assert "skill-tree" in live
    assert "shopify-conjure" not in live
    # Filter correctness: all wip projects must be excluded from live.
    for name, project in registry.projects.items():
        if project.status == "wip":
            assert name not in live, f"{name} is wip but leaked into live_projects()"


def test_project_channel_names_list_form() -> None:
    p = Project(
        repo="https://example.com/x",
        kind="mcp-server",
        audience="mcp-users",
        status="live",
        problem="p",
        solution_one_liner="s",
        facts=[],
        angles=[],
        channels=["bluesky", "devto"],
    )
    assert p.channel_names == ["bluesky", "devto"]
    assert p.weight_for("bluesky") == 1.0


def test_project_channel_names_dict_form() -> None:
    p = Project(
        repo="https://example.com/x",
        kind="mcp-server",
        audience="mcp-users",
        status="live",
        problem="p",
        solution_one_liner="s",
        facts=[],
        angles=[],
        channels={"bluesky": {"weight": 1.5, "rolling_score": 2.1}, "devto": {"weight": 0.3}},  # type: ignore[arg-type]
    )
    assert set(p.channel_names) == {"bluesky", "devto"}
    assert p.weight_for("bluesky") == 1.5
    assert p.weight_for("devto") == 0.3


def test_konid_has_facts() -> None:
    """Honesty backstop: the live konid project must have facts[] populated."""
    registry = load(REPO_ROOT / "projects.yml")
    konid = registry.get("konid")
    assert len(konid.facts) >= 3, "live project must have at least 3 grounding facts"
    assert konid.problem, "live project must have a problem statement"
    assert konid.solution_one_liner, "live project must have a solution one-liner"


def test_rabbitholes_has_facts() -> None:
    registry = load(REPO_ROOT / "projects.yml")
    rh = registry.get("rabbitholes")
    assert len(rh.facts) >= 3
    assert len(rh.angles) >= 3


def test_wip_projects_allowed_empty_facts() -> None:
    """WIP placeholders should load without failing validation even with empty facts."""
    registry = load(REPO_ROOT / "projects.yml")
    placeholder = registry.get("shopify-conjure")
    assert placeholder.status == "wip"
    assert placeholder.facts == []
