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
from pipeline.registry import Angle, Project, load
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


def _pick_next_project(
    live: dict[str, Project],
    manifest: list[dict],
) -> str | None:
    """Pick the next project to post: skip projects already posted today,
    then pick the one with the oldest most-recent post (or never posted)."""
    today = date.today().isoformat()
    posted_today = {e["project"] for e in manifest if e.get("posted_at") == today}

    candidates = [name for name in live if name not in posted_today]
    if not candidates:
        return None  # All projects already posted today

    # Among candidates, pick the one with the oldest last post (or never posted)
    def last_posted(name: str) -> str:
        project_posts = [e for e in manifest if e.get("project") == name]
        if not project_posts:
            return ""  # Never posted — highest priority
        return max(e.get("posted_at", "") for e in project_posts)

    candidates.sort(key=last_posted)
    return candidates[0]


def _cmd_cycle(args: argparse.Namespace) -> int:
    """Daily cycle: pick one project, draft + post to all its channels."""
    from pipeline.drafter import draft
    from pipeline.publish import get_publisher
    from pipeline.registry import load_raw, save_raw
    from pipeline.report import add_to_manifest, load_manifest, previous_posts_for

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

    # Pick one project for this invocation
    manifest = load_manifest()
    name = _pick_next_project(live, manifest)
    if name is None:
        print("All live projects already posted today. Nothing to do.")
        return 0

    project = live[name]
    resolved = surfaces.resolve(project)
    channels = resolved.daily_channels
    if not channels or not project.angles:
        print(f"No channels or angles for {name}, skipping.", file=sys.stderr)
        return 1

    angle = _pick_next_angle(project.angles)
    history = previous_posts_for(name, limit=3)

    print(f"=== {name} | angle={angle.id} | channels={','.join(channels)} ===")

    if args.dry_run:
        for ch in channels:
            print(f"  [dry run] Would draft + post to {ch}")
        print(f"\nCycle complete: {name} → {len(channels)} channel(s) (dry run).")
        return 0

    posted = 0
    for channel in channels:
        print(f"\n--- {name} | {channel} ---")

        result = draft(
            project, name, angle.id, channel, config,
            previous_posts=history,
        )
        best = result.best
        if not best:
            print("  No drafts passed validation.", file=sys.stderr)
            continue

        print(f"  Draft: {best.text[:100]}...")

        try:
            publisher = get_publisher(channel)
        except ValueError:
            print(f"  No publisher for '{channel}', skipping.", file=sys.stderr)
            continue

        post_result = publisher.publish(best.text, config)
        if post_result.success:
            print(f"  Posted: {post_result.url or post_result.error}")
            posted += 1

            posted_dir = Path("content") / "posted"
            posted_dir.mkdir(parents=True, exist_ok=True)
            posted_path = posted_dir / f"{channel}_{date.today().isoformat()}_{name}.md"
            posted_path.write_text(best.text)

            add_to_manifest(
                project=name,
                channel=channel,
                url=post_result.url or "",
                angle=angle.id,
            )

            # Add to history so subsequent channels in this run see it
            history.insert(0, best.text)
        else:
            print(f"  Failed: {post_result.error}", file=sys.stderr)

    # Persist angle last_used back to projects.yml
    if posted > 0:
        raw_doc = load_raw(args.projects)
        today_str = date.today().isoformat()
        if name in raw_doc:
            for a in raw_doc[name].get("angles", []):
                if a["id"] == angle.id:
                    a["last_used"] = today_str
        save_raw(raw_doc, args.projects)

    print(f"\nCycle complete: {name} → {posted}/{len(channels)} channel(s).")
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

    print(f"Fetching README from {args.repo}...")
    readme = fetch_readme(args.repo)
    print(f"  Got {len(readme)} chars.")

    # Load pain research context if provided
    pain_context = None
    if args.pain_context:
        pain_path = Path(args.pain_context)
        if pain_path.exists():
            pain_context = pain_path.read_text()
            print(f"  Loaded {len(pain_context)} chars of pain research from {pain_path}")
        else:
            print(f"  Warning: --pain-context file not found: {pain_path}", file=sys.stderr)

    print("  Generating project entry via Claude...")
    entry = generate_entry(
        readme, args.repo, config,
        kind=args.kind, audience=args.audience,
        pain_context=pain_context,
    )

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
        if payload is None:
            print("\nNo posts to report — skipping Slack.")
        elif send_slack(payload, webhook):
            print("\nSlack notification sent.")
        else:
            print("\nSlack notification failed.", file=sys.stderr)

    return 0


def _cmd_setup(args: argparse.Namespace) -> int:
    """Check credentials and guide through setup."""
    from pipeline.setup import run_setup
    return run_setup()


def _cmd_status(args: argparse.Namespace) -> int:
    """Show pipeline status: projects, posts, next actions."""
    from pipeline.report import load_manifest

    registry = load(args.projects)
    live = registry.live_projects()
    manifest = load_manifest()

    print("Pipeline Status\n")
    print(f"  Projects: {len(live)} live, {len(registry.projects) - len(live)} other")
    for name, project in live.items():
        posts = [p for p in manifest if p["project"] == name]
        channels = [p["channel"] for p in posts]
        print(f"    {name}: {len(project.angles)} angles, {len(posts)} posts ({', '.join(channels) or 'none yet'})")

    print(f"\n  Total posts tracked: {len(manifest)}")
    if manifest:
        latest = manifest[-1]
        print(f"  Latest: {latest['project']}/{latest['channel']} on {latest.get('posted_at', '?')}")

    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    """Validate a draft through the anti-slop gate."""
    from pipeline.antislop import validate

    if args.file:
        draft_text = Path(args.file).read_text().strip()
    else:
        draft_text = sys.stdin.read().strip()

    if not draft_text:
        print("Error: empty draft.", file=sys.stderr)
        return 1

    result = validate(draft_text, channel=args.channel)

    if result.passed:
        print("PASSED")
        if result.warnings:
            for v in result.warnings:
                print(f"  [~] {v.rule}: {v.detail}")
        return 0
    else:
        print("FAILED")
        for v in result.violations:
            marker = "X" if v.severity == "hard" else "~"
            print(f"  [{marker}] {v.rule}: {v.detail}")
        return 1


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
    p_post.add_argument("--project", type=str, default=None, help="Project name for manifest tracking")
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
    p_onboard.add_argument("--kind", type=str, default=None,
                           help="Auto-detected from README if omitted")
    p_onboard.add_argument("--audience", type=str, default=None)
    p_onboard.add_argument("--pain-context", type=str, default=None,
                           help="Path to a file with real user pain statements from research")
    p_onboard.set_defaults(func=_cmd_onboard)

    p_validate = sub.add_parser("validate", help="Run anti-slop gate on a draft.")
    p_validate.add_argument("--file", type=str, default=None, help="Path to draft (or stdin)")
    p_validate.add_argument("--channel", type=str, default=None, help="Channel for length checks")
    p_validate.set_defaults(func=_cmd_validate)

    p_report = sub.add_parser("report", help="Fetch engagement metrics and generate report.")
    p_report.set_defaults(func=_cmd_report)

    p_setup = sub.add_parser("setup", help="Check credentials and guide through setup.")
    p_setup.set_defaults(func=_cmd_setup)

    p_status = sub.add_parser("status", help="Show pipeline status: projects, posts, next actions.")
    p_status.set_defaults(func=_cmd_status)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
