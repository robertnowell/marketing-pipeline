"""Daily engagement report — fetch metrics, save history, generate digest.

Reads the posted manifest, fetches current engagement from each platform,
saves a dated snapshot, and returns a formatted report suitable for Slack
or terminal output.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from ruamel.yaml import YAML

from pipeline.config import Config
from pipeline.metrics import PostMetrics, fetch_metrics

_yaml = YAML()
_yaml.default_flow_style = False

MANIFEST_PATH = Path("content/posted/manifest.yml")
METRICS_DIR = Path("reports/metrics")


def load_manifest() -> list[dict]:
    """Load the posted content manifest."""
    if not MANIFEST_PATH.exists():
        return []
    data = _yaml.load(MANIFEST_PATH.read_text())
    return data if isinstance(data, list) else []


def save_manifest(entries: list[dict]) -> None:
    """Save the posted content manifest."""
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST_PATH.open("w") as f:
        _yaml.dump(entries, f)


def add_to_manifest(
    project: str, channel: str, url: str, angle: str = "",
) -> None:
    """Append a posted item to the manifest."""
    entries = load_manifest()
    entries.append({
        "project": project,
        "channel": channel,
        "url": url,
        "angle": angle,
        "posted_at": date.today().isoformat(),
    })
    save_manifest(entries)


def generate_report(config: Config) -> list[PostMetrics]:
    """Fetch metrics for all posted content and save a snapshot."""
    manifest = load_manifest()
    if not manifest:
        return []

    results = []
    for post in manifest:
        if not post.get("url"):
            continue
        metrics = fetch_metrics(post, config)
        results.append(metrics)

    # Save snapshot
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    snapshot_path = METRICS_DIR / f"{date.today().isoformat()}.yml"
    snapshot = [m.to_dict() for m in results]
    with snapshot_path.open("w") as f:
        _yaml.dump(snapshot, f)

    return results


def format_report(results: list[PostMetrics]) -> str:
    """Format metrics into a readable report."""
    if not results:
        return "No posted content to report on."

    lines = [f"Engagement Report — {date.today().isoformat()}", ""]

    # Summary
    total_engagement = sum(m.engagement for m in results)
    total_views = sum(m.views for m in results)
    lines.append(f"Total: {total_engagement} engagements, {total_views} views across {len(results)} posts")
    lines.append("")

    # Per-post breakdown, sorted by engagement descending
    sorted_results = sorted(results, key=lambda m: m.engagement, reverse=True)
    for m in sorted_results:
        status = f"{m.likes}L {m.reposts}R {m.replies}C"
        if m.views:
            status += f" {m.views}V"
        if m.error:
            status = f"error: {m.error[:60]}"
        lines.append(f"  {m.channel:<10} {m.project:<15} {status}")
        lines.append(f"             {m.url}")

    # Top performer
    if sorted_results and sorted_results[0].engagement > 0:
        top = sorted_results[0]
        lines.append("")
        lines.append(f"Top: {top.project}/{top.channel} ({top.engagement} engagements)")

    return "\n".join(lines)


def format_slack_report(results: list[PostMetrics]) -> dict | None:
    """Format metrics as a Slack webhook payload. Returns None if nothing to report."""
    if not results:
        return None  # Don't send empty reports

    total_engagement = sum(m.engagement for m in results)
    total_views = sum(m.views for m in results)
    today = date.today().isoformat()

    # Group by project
    by_project: dict[str, list[PostMetrics]] = {}
    for m in results:
        by_project.setdefault(m.project, []).append(m)

    # Today's posts
    today_posts = [m for m in results if m.posted_at == today]

    # Build a single compact text block (more readable in Slack than blocks API)
    lines = [f"*Marketing Pipeline — {today}*"]
    lines.append("")

    # Summary line
    lines.append(
        f"{total_engagement} engagements, {total_views} views across "
        f"{len(results)} posts in {len(by_project)} projects"
    )

    # Per-project summary (compact)
    lines.append("")
    for proj, metrics in sorted(by_project.items()):
        proj_eng = sum(m.engagement for m in metrics)
        proj_views = sum(m.views for m in metrics)
        channels = ", ".join(sorted({m.channel for m in metrics}))
        parts = []
        if proj_eng:
            parts.append(f"{proj_eng} eng")
        if proj_views:
            parts.append(f"{proj_views} views")
        stats = " | ".join(parts) if parts else "no engagement yet"
        lines.append(f"*{proj}* ({channels}) — {stats}")

    # Top performer (only if there's actual engagement)
    top = max(results, key=lambda m: m.engagement)
    if top.engagement > 0:
        lines.append("")
        lines.append(f"Top: <{top.url}|{top.project}/{top.channel}> ({top.engagement} eng)")

    # What was posted today
    if today_posts:
        lines.append("")
        lines.append(f"_Posted today: {len(today_posts)} new_")
        for m in today_posts:
            lines.append(f"  <{m.url}|{m.project} → {m.channel}>")

    return {"text": "\n".join(lines)}


def send_slack(payload: dict, webhook_url: str) -> bool:
    """Send a report to Slack via incoming webhook."""
    import httpx

    try:
        resp = httpx.post(webhook_url, json=payload, timeout=10)
        return resp.status_code == 200
    except Exception:
        return False
