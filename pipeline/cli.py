"""Command-line entry point for the marketing pipeline.

Subcommands:
  plan             print loaded registry summary (dry, no network)
  surfaces         print a project's resolved channel + directory set
  watering-holes   print a project's resolved watering-hole set
  draft            generate post drafts for a project+angle+channel
  post             publish a validated draft to a channel
  launch           run directory lister for a project
  cycle            daily loop: pick next rotation, draft, validate, post
  onboard          scaffold a new project entry in projects.yml
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from pipeline.config import Config
from pipeline.registry import Angle, load
from pipeline.surfaces import SurfaceRegistry

# --- Existing commands (unchanged) ---


def _cmd_surfaces(args: argparse.Namespace) -> int:
    registry = load(args.projects)
    surfaces = SurfaceRegistry.load(args.surfaces)

    if args.project:
        projects = {args.project: registry.get(args.project)}
    else:
        projects = registry.live_projects()

    for name, project in projects.items():
        resolved = surfaces.resolve(project)
        print(f"\n\u258e {name}  (audience={project.audience}, kind={project.kind})")
        print(f"  daily_channels: {resolved.daily_channels}")
        print(f"  directories ({len(resolved.directories)}):")
        for d in resolved.directories:
            target = d.repo or d.url or d.tool or d.contact or "?"
            print(f"    - {d.name} [{d.type}] \u2192 {target}")
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
    registry = load(args.projects)
    surfaces = SurfaceRegistry.load(args.surfaces)

    if args.project:
        projects = {args.project: registry.get(args.project)}
    else:
        projects = registry.live_projects()

    for name, project in projects.items():
        resolved = surfaces.resolve(project)
        print(f"\n\u258e {name}  (audience={project.audience}, kind={project.kind})")
        if not resolved.watering_holes:
            print("  (no watering holes configured for this audience yet)")
            continue
        for entry in resolved.watering_holes:
            print(f"  - {json.dumps(entry)}")
    return 0


# --- New commands ---


def _cmd_draft(args: argparse.Namespace) -> int:
    """Generate draft posts for a project+angle+channel."""
    from pipeline.drafter import draft

    registry = load(args.projects)
    project = registry.get(args.project)
    config = Config.from_env()

    # Pick angle: explicit or first available
    if args.angle:
        angle_id = args.angle
    elif project.angles:
        angle_id = project.angles[0].id
    else:
        print(f"Error: project '{args.project}' has no angles defined.", file=sys.stderr)
        return 1

    # Pick channel: explicit or first daily channel
    if args.channel:
        channel = args.channel
    else:
        surfaces = SurfaceRegistry.load(args.surfaces)
        resolved = surfaces.resolve(project)
        if resolved.daily_channels:
            channel = resolved.daily_channels[0]
        else:
            print(f"Error: no daily channels for '{args.project}'.", file=sys.stderr)
            return 1

    print(f"Drafting for {args.project} | angle={angle_id} | channel={channel}")
    result = draft(project, args.project, angle_id, channel, config)

    for c in result.candidates:
        status = "PASS" if c.validation.passed else "FAIL"
        print(f"\n--- Candidate #{c.rank} [{status}] ---")
        print(c.text)
        if c.validation.violations:
            for v in c.validation.violations:
                marker = "X" if v.severity == "hard" else "~"
                print(f"  [{marker}] {v.rule}: {v.detail}")

    best = result.best
    if best:
        print(f"\nBest candidate: #{best.rank}")
        # Save to content/drafts/
        drafts_dir = Path("content") / "drafts" / args.project / channel
        drafts_dir.mkdir(parents=True, exist_ok=True)
        draft_path = drafts_dir / f"{angle_id}_{date.today().isoformat()}.md"
        draft_path.write_text(best.text)
        print(f"Saved to: {draft_path}")
    else:
        print("\nNo candidates passed validation.", file=sys.stderr)
        return 1

    return 0


def _cmd_post(args: argparse.Namespace) -> int:
    """Publish a draft to a channel."""
    from pipeline.publish import get_publisher

    config = Config.from_env()
    config = Config(
        anthropic_api_key=config.anthropic_api_key,
        bluesky=config.bluesky,
        devto=config.devto,
        hashnode=config.hashnode,
        mastodon=config.mastodon,
        dry_run=args.dry_run,
    )

    # Read draft from file or stdin
    if args.file:
        draft_text = Path(args.file).read_text().strip()
    else:
        print("Reading draft from stdin (Ctrl+D to finish):", file=sys.stderr)
        draft_text = sys.stdin.read().strip()

    if not draft_text:
        print("Error: empty draft.", file=sys.stderr)
        return 1

    publisher = get_publisher(args.channel)
    result = publisher.publish(draft_text, config)

    if result.success:
        print(f"Posted to {result.channel}: {result.url or result.error}")
        if result.url:
            from pipeline.report import add_to_manifest

            posted_dir = Path("content") / "posted"
            posted_dir.mkdir(parents=True, exist_ok=True)
            posted_path = posted_dir / f"{args.channel}_{date.today().isoformat()}.md"
            posted_path.write_text(draft_text)
            # Track in manifest for metrics
            add_to_manifest(
                project=getattr(args, "project", "unknown"),
                channel=args.channel,
                url=result.url,
            )
    else:
        print(f"Failed to post to {result.channel}: {result.error}", file=sys.stderr)
        return 1

    return 0


def _cmd_launch(args: argparse.Namespace) -> int:
    """Run directory lister for a project — submit to all relevant directories."""
    from pipeline.lister import execute_automated, plan_listings, save_listing_status

    registry = load(args.projects)
    project = registry.get(args.project)

    plan = plan_listings(project, args.project)

    print(f"\nListing plan for {args.project} ({len(plan.submissions)} directories):")
    print(f"\n  Automated ({len(plan.automated)}):")
    for sub in plan.automated:
        print(f"    - {sub.directory}: {sub.command}")

    print(f"\n  Manual ({len(plan.manual)}):")
    for sub in plan.manual:
        url = sub.url or "(see notes)"
        print(f"    - {sub.directory}: {url}")
        if sub.notes:
            print(f"      {sub.notes}")

    if not args.dry_run and plan.automated:
        print(f"\nExecuting {len(plan.automated)} automated submissions...")
        results = execute_automated(plan, dry_run=False)
        for name, success, output in results:
            status = "OK" if success else "FAIL"
            print(f"  [{status}] {name}: {output[:120]}")
    else:
        results = execute_automated(plan, dry_run=True)
        for name, _success, output in results:
            print(f"  [dry run] {name}: {output}")

    status_path = save_listing_status(plan, results)
    print(f"\nListing status saved to: {status_path}")
    return 0


def _cmd_cycle(args: argparse.Namespace) -> int:
    """Daily cycle: pick next angle/channel rotation, draft, validate, post."""
    from pipeline.drafter import draft
    from pipeline.publish import get_publisher

    registry = load(args.projects)
    surfaces = SurfaceRegistry.load(args.surfaces)
    config = Config.from_env()
    config = Config(
        anthropic_api_key=config.anthropic_api_key,
        bluesky=config.bluesky,
        devto=config.devto,
        hashnode=config.hashnode,
        mastodon=config.mastodon,
        dry_run=args.dry_run,
    )

    live = registry.live_projects()
    if not live:
        print("No live projects.", file=sys.stderr)
        return 1

    posted = 0
    for name, project in live.items():
        resolved = surfaces.resolve(project)
        channels = resolved.daily_channels
        if not channels or not project.angles:
            continue

        # Simple rotation: pick the angle with the oldest last_used date
        angle = _pick_next_angle(project.angles)
        # Post to first available channel (rotate channels across days in future)
        channel = channels[0]

        print(f"\n--- {name} | angle={angle.id} | channel={channel} ---")
        result = draft(project, name, angle.id, channel, config)
        best = result.best
        if not best:
            print(f"  No drafts passed validation for {name}.", file=sys.stderr)
            continue

        print(f"  Draft: {best.text[:100]}...")

        try:
            publisher = get_publisher(channel)
        except ValueError:
            print(f"  No publisher for channel '{channel}', skipping.", file=sys.stderr)
            continue

        post_result = publisher.publish(best.text, config)
        if post_result.success:
            print(f"  Posted: {post_result.url or post_result.error}")
            posted += 1
        else:
            print(f"  Failed: {post_result.error}", file=sys.stderr)

    print(f"\nCycle complete: {posted} post(s).")
    return 0


def _cmd_onboard(args: argparse.Namespace) -> int:
    """Auto-onboard a new project: fetch README, generate problem/angles via Claude."""
    from ruamel.yaml import YAML

    from pipeline.onboard import fetch_readme, generate_entry

    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)

    projects_path = Path(args.projects)
    doc = yaml.load(projects_path.read_text()) or {}

    if args.name in doc:
        print(f"Project '{args.name}' already exists in {projects_path}.", file=sys.stderr)
        return 1

    config = Config.from_env()
    audience = args.audience or "claude-code-users"

    print(f"Fetching README from {args.repo}...")
    readme = fetch_readme(args.repo)
    print(f"  Got {len(readme)} chars. Generating project entry via Claude...")

    entry = generate_entry(readme, args.repo, args.kind, audience, config)

    doc[args.name] = entry

    with projects_path.open("w") as f:
        yaml.dump(doc, f)

    print(f"\nOnboarded '{args.name}' in {projects_path}.")
    print(f"  problem: {entry['problem'][:80]}...")
    print(f"  solution: {entry['solution_one_liner'][:80]}...")
    print(f"  facts: {len(entry['facts'])} extracted")
    print(f"  angles: {len(entry['angles'])} generated")
    print("\nReady to go:")
    print(f"  marketing draft --project {args.name} --channel bluesky")
    print(f"  marketing launch --project {args.name} --dry-run")
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    """Fetch engagement metrics and generate a report."""
    from pipeline.report import format_report, format_slack_report, generate_report, send_slack

    config = Config.from_env()
    print("Fetching engagement metrics...")
    results = generate_report(config)

    report = format_report(results)
    print(f"\n{report}")

    # Send to Slack if webhook configured
    import os

    webhook = os.environ.get("SLACK_WEBHOOK_URL")
    if webhook:
        payload = format_slack_report(results)
        if send_slack(payload, webhook):
            print("\nSlack notification sent.")
        else:
            print("\nSlack notification failed.", file=sys.stderr)

    return 0


def _pick_next_angle(angles: list[Angle]) -> Angle:
    """Pick the angle with the oldest (or None) last_used date."""
    unused = [a for a in angles if a.last_used is None]
    if unused:
        return unused[0]
    return sorted(angles, key=lambda a: a.last_used or date.min)[0]


# --- CLI wiring ---


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="marketing", description="OSS marketing pipeline CLI")
    parser.add_argument("--projects", type=Path, default=Path("projects.yml"))
    parser.add_argument("--surfaces", type=Path, default=Path("surfaces.yml"))

    sub = parser.add_subparsers(dest="command", required=True)

    # Existing commands
    p_surfaces = sub.add_parser("surfaces", help="Print a project's resolved surface set.")
    p_surfaces.add_argument("--project", type=str, default=None)
    p_surfaces.set_defaults(func=_cmd_surfaces)

    p_plan = sub.add_parser("plan", help="Dry run: summarize loaded registry.")
    p_plan.set_defaults(func=_cmd_plan)

    p_wh = sub.add_parser("watering-holes", help="Print a project's resolved watering hole set.")
    p_wh.add_argument("--project", type=str, default=None)
    p_wh.set_defaults(func=_cmd_watering_holes)

    # New commands
    p_draft = sub.add_parser("draft", help="Generate post drafts for a project.")
    p_draft.add_argument("--project", type=str, required=True)
    p_draft.add_argument("--angle", type=str, default=None)
    p_draft.add_argument("--channel", type=str, default=None)
    p_draft.set_defaults(func=_cmd_draft)

    p_post = sub.add_parser("post", help="Publish a draft to a channel.")
    p_post.add_argument("--channel", type=str, required=True)
    p_post.add_argument("--file", type=str, default=None, help="Path to draft file")
    p_post.add_argument("--dry-run", action="store_true")
    p_post.set_defaults(func=_cmd_post)

    p_launch = sub.add_parser("launch", help="Submit project to all relevant directories.")
    p_launch.add_argument("--project", type=str, required=True)
    p_launch.add_argument("--dry-run", action="store_true")
    p_launch.set_defaults(func=_cmd_launch)

    p_cycle = sub.add_parser("cycle", help="Daily loop: draft + post for all live projects.")
    p_cycle.add_argument("--dry-run", action="store_true")
    p_cycle.set_defaults(func=_cmd_cycle)

    p_onboard = sub.add_parser("onboard", help="Scaffold a new project entry.")
    p_onboard.add_argument("--name", type=str, required=True)
    p_onboard.add_argument("--repo", type=str, required=True, help="owner/repo")
    p_onboard.add_argument("--kind", type=str, required=True,
                           help="mcp-server, claude-skill, browser-extension, etc.")
    p_onboard.add_argument("--audience", type=str, default=None)
    p_onboard.set_defaults(func=_cmd_onboard)

    p_report = sub.add_parser("report", help="Fetch engagement metrics and generate report.")
    p_report.set_defaults(func=_cmd_report)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
