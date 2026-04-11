"""Command-line entry point for the marketing pipeline.

Subcommands grow over the weeks outlined in the demand-capture reframe plan:
  plan             print loaded registry summary (dry, no network)
  surfaces         print a project's resolved channel + directory set
  watering-holes   print a project's resolved watering-hole set (for safari)
  safari           [Week 3] harvest pain/jargon/recs from watering holes
  listen           [Week 3] poll active surfaces for project-matching complaints
  seo              [Week 4] weekly long-tail SEO page generator
  ebomb            [Week 4] monthly long-form post generator (per project)
  evaluate         [Week 3] refresh stars.csv + rebalance pain-phrase priorities
  launch           [Week 4] one-shot directory launch workflow per project

Weeks 1-2 scope: plan, surfaces, watering-holes.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pipeline.registry import load
from pipeline.surfaces import SurfaceRegistry


def _cmd_surfaces(args: argparse.Namespace) -> int:
    registry = load(args.projects)
    surfaces = SurfaceRegistry.load(args.surfaces)

    if args.project:
        projects = {args.project: registry.get(args.project)}
    else:
        projects = registry.live_projects()

    for name, project in projects.items():
        resolved = surfaces.resolve(project)
        print(f"\n▎ {name}  (audience={project.audience}, kind={project.kind})")
        print(f"  daily_channels: {resolved.daily_channels}")
        print(f"  directories ({len(resolved.directories)}):")
        for d in resolved.directories:
            target = d.repo or d.url or d.tool or d.contact or "?"
            print(f"    - {d.name} [{d.type}] → {target}")
        print(f"  forums_manual: {resolved.forums_manual}")
        print(f"  watering_holes ({len(resolved.watering_holes)}): "
              f"see `watering-holes --project {name}` for full detail")
    return 0


def _cmd_plan(args: argparse.Namespace) -> int:
    registry = load(args.projects)
    surfaces = SurfaceRegistry.load(args.surfaces)
    live = registry.live_projects()

    print(f"Loaded {len(live)} live project(s) (of {len(registry.projects)} total).")
    for name, project in live.items():
        resolved = surfaces.resolve(project)
        print(f"  {name}: {len(project.angles)} angle(s), "
              f"{len(resolved.daily_channels)} daily channel(s), "
              f"{len(resolved.directories)} launch directory target(s), "
              f"{len(resolved.watering_holes)} watering hole(s)")
    return 0


def _cmd_watering_holes(args: argparse.Namespace) -> int:
    """Print the resolved watering-hole set for a project (or all live projects).

    This is a read-only inspection command. Every entry is a dict with a `type`
    discriminator (hn_algolia, reddit_search, github_issues, bluesky_search, so_tag).
    Week 3 safari.py will dispatch on `type` to hit the actual endpoint.
    """
    registry = load(args.projects)
    surfaces = SurfaceRegistry.load(args.surfaces)

    if args.project:
        projects = {args.project: registry.get(args.project)}
    else:
        projects = registry.live_projects()

    for name, project in projects.items():
        resolved = surfaces.resolve(project)
        print(f"\n▎ {name}  (audience={project.audience}, kind={project.kind})")
        if not resolved.watering_holes:
            print("  (no watering holes configured for this audience yet)")
            continue
        for entry in resolved.watering_holes:
            # Pretty-print as one line per entry.
            print(f"  - {json.dumps(entry)}")
    return 0


def _cmd_not_yet_built(command: str, week: str) -> int:
    raise NotImplementedError(
        f"`{command}` is not yet wired. Scheduled for {week} per the demand-capture "
        f"reframe plan at ~/.claude/plans/adaptive-booping-dahl.md."
    )


def _cmd_safari(args: argparse.Namespace) -> int:
    return _cmd_not_yet_built("safari", "Week 3")


def _cmd_listen(args: argparse.Namespace) -> int:
    return _cmd_not_yet_built("listen", "Week 3")


def _cmd_seo(args: argparse.Namespace) -> int:
    return _cmd_not_yet_built("seo", "Week 4")


def _cmd_ebomb(args: argparse.Namespace) -> int:
    return _cmd_not_yet_built("ebomb", "Week 4")


def _cmd_evaluate(args: argparse.Namespace) -> int:
    return _cmd_not_yet_built("evaluate", "Week 3")


def _cmd_launch(args: argparse.Namespace) -> int:
    return _cmd_not_yet_built("launch", "Week 4")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="marketing", description="OSS marketing pipeline CLI")
    parser.add_argument("--projects", type=Path, default=Path("projects.yml"))
    parser.add_argument("--surfaces", type=Path, default=Path("surfaces.yml"))

    sub = parser.add_subparsers(dest="command", required=True)

    p_surfaces = sub.add_parser("surfaces", help="Print a project's resolved surface set.")
    p_surfaces.add_argument("--project", type=str, default=None)
    p_surfaces.set_defaults(func=_cmd_surfaces)

    p_plan = sub.add_parser("plan", help="Dry run: summarize loaded registry.")
    p_plan.set_defaults(func=_cmd_plan)

    p_wh = sub.add_parser("watering-holes", help="Print a project's resolved watering hole set.")
    p_wh.add_argument("--project", type=str, default=None)
    p_wh.set_defaults(func=_cmd_watering_holes)

    # Week 3-4 stubs. Register so `--help` lists them; actual call raises
    # NotImplementedError with a pointer to the plan file.
    for cmd_name, func in [
        ("safari", _cmd_safari),
        ("listen", _cmd_listen),
        ("seo", _cmd_seo),
        ("ebomb", _cmd_ebomb),
        ("evaluate", _cmd_evaluate),
        ("launch", _cmd_launch),
    ]:
        p = sub.add_parser(cmd_name, help=f"[stub — not yet built] {cmd_name}")
        p.add_argument("--project", type=str, default=None)
        p.add_argument("--dry-run", action="store_true")
        p.set_defaults(func=func)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
