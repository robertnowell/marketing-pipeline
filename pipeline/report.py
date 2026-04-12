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


def format_slack_report(results: list[PostMetrics]) -> dict:
    """Format metrics as a Slack webhook payload."""
    if not results:
        return {
            "text": f"Marketing Pipeline — {date.today().isoformat()}\nNo posts to report.",
        }

    total_engagement = sum(m.engagement for m in results)
    total_views = sum(m.views for m in results)
    sorted_results = sorted(results, key=lambda m: m.engagement, reverse=True)

    blocks = []

    # Header
    blocks.append({
        "type": "header",
        "text": {"type": "plain_text", "text": f"Daily Engagement — {date.today().isoformat()}"},
    })

    # Summary
    summary = f"*{total_engagement}* engagements, *{total_views}* views across *{len(results)}* posts"
    blocks.append({
        "type": "section",
        "text": {"type": "mrkdwn", "text": summary},
    })

    blocks.append({"type": "divider"})

    # Per-post
    for m in sorted_results[:10]:  # Top 10
        if m.error:
            text = f"*{m.project}* ({m.channel}) — error fetching metrics"
        else:
            parts = [f"{m.likes} likes", f"{m.reposts} reposts", f"{m.replies} replies"]
            if m.views:
                parts.append(f"{m.views} views")
            text = f"*{m.project}* ({m.channel}) — {', '.join(parts)}\n<{m.url}>"
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": text},
        })

    return {"blocks": blocks}


def send_slack(payload: dict, webhook_url: str) -> bool:
    """Send a report to Slack via incoming webhook."""
    import httpx

    try:
        resp = httpx.post(webhook_url, json=payload, timeout=10)
        return resp.status_code == 200
    except Exception:
        return False
