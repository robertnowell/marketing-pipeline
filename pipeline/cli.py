"""Command-line entry point for the marketing pipeline.

Subcommands will grow over the weeks outlined in the plan:
  plan          print today's work items (dry, no network)
  surfaces      print a project's resolved channel + directory set
  run-daily     draft + validate + antislop + publish (Week 3)
  launch        run per-project launch one-shot via Managed Agents (Week 4)
  digest        produce daily reply/mention summary (Week 3)
  evaluate      refresh stars.csv + rebalance weights (Week 3)

Week 1 scope is `plan` and `surfaces` only.
"""

from __future__ import annotations

import argparse
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
              f"{len(resolved.directories)} launch directory target(s)")
    return 0


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

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
