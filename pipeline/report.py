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
    source_id: str = "",
) -> None:
    """Append a posted item to the manifest.

    source_id uniquely identifies the source content (e.g., Kopi email ID)
    so dedup works even when the same content is posted via different URLs.
    """
    entries = load_manifest()
    entries.append({
        "project": project,
        "channel": channel,
        "url": url,
        "angle": angle,
        "source_id": source_id,
        "posted_at": date.today().isoformat(),
    })
    save_manifest(entries)


def is_already_posted(source_id: str) -> bool:
    """Check if content with this source_id has already been posted."""
    if not source_id:
        return False
    manifest = load_manifest()
    return any(entry.get("source_id") == source_id for entry in manifest)


def previous_posts_for(project: str, limit: int = 3) -> list[str]:
    """Return up to `limit` most recent posted texts for a project, newest first."""
    manifest = load_manifest()
    # Filter to this project, most recent first
    project_entries = [
        e for e in reversed(manifest) if e.get("project") == project
    ][:limit]

    posted_dir = Path("content/posted")
    texts = []
    for entry in project_entries:
        channel = entry.get("channel", "")
        posted_at = entry.get("posted_at", "")
        proj = entry.get("project", "")
        # Try new naming convention first (channel_date_project.md),
        # fall back to old (channel_date.md)
        candidates = [
            posted_dir / f"{channel}_{posted_at}_{proj}.md",
            posted_dir / f"{channel}_{posted_at}.md",
        ]
        for path in candidates:
            if path.exists():
                texts.append(path.read_text().strip())
                break
    return texts


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
    """Format metrics as a Slack webhook payload. Returns None if nothing to report.

    Structure (optimized for a morning scan):
      1. Headline summary line.
      2. "What got engagement" — per-post lines with breakdown + link.
         Only shown when at least one post has engagement > 0.
      3. "By project" rollup — projects sorted by engagement desc.
      4. "Posted today" — per-project line with inline links to each channel.
    """
    if not results:
        return None  # Don't send empty reports

    total_engagement = sum(m.engagement for m in results)
    total_views = sum(m.views for m in results)
    today = date.today().isoformat()

    by_project: dict[str, list[PostMetrics]] = {}
    for m in results:
        by_project.setdefault(m.project, []).append(m)

    today_posts = [m for m in results if m.posted_at == today]
    engaged = sorted(
        (m for m in results if m.engagement > 0),
        key=lambda m: m.engagement,
        reverse=True,
    )
    failing = sorted(
        (m for m in results if m.error),
        key=lambda m: (m.channel, m.posted_at or ""),
    )

    lines: list[str] = [f"*Marketing Pipeline — {today}*"]
    tail = f" · {len(failing)} failing" if failing else ""
    lines.append(
        f"{total_engagement} eng · {total_views} views · "
        f"{len(results)} posts · {len(by_project)} projects{tail}"
    )

    # --- 1. What got engagement (per-post, with links)
    if engaged:
        lines.append("")
        lines.append(f"*What got engagement* ({len(engaged)} of {len(results)})")
        for m in engaged:
            lines.append(_engaged_line(m))

    # --- 1b. Can't fetch metrics (failed posts — surface, don't hide)
    if failing:
        lines.append("")
        lines.append(f"*Can't fetch metrics* ({len(failing)} of {len(results)})")
        for m in failing:
            lines.append(_failing_line(m))

    # --- 2. By project (engagement-sorted rollup)
    lines.append("")
    lines.append("*By project*")
    proj_sorted = sorted(
        by_project.items(),
        key=lambda kv: (
            -sum(m.engagement for m in kv[1]),
            -sum(m.views for m in kv[1]),
            kv[0],
        ),
    )
    for proj, metrics in proj_sorted:
        p_eng = sum(m.engagement for m in metrics)
        p_views = sum(m.views for m in metrics)
        parts = []
        if p_eng:
            parts.append(f"{p_eng} eng")
        if p_views:
            parts.append(f"{p_views} views")
        summary = " · ".join(parts) if parts else "no engagement yet"
        lines.append(f"• *{proj}* — {summary}")

    # --- 3. Posted today (one line per project, channel links inline)
    if today_posts:
        today_by_project: dict[str, list[PostMetrics]] = {}
        for m in today_posts:
            today_by_project.setdefault(m.project, []).append(m)

        lines.append("")
        lines.append(
            f"*Posted today* ({len(today_posts)} posts · {len(today_by_project)} projects)"
        )
        for proj in sorted(today_by_project.keys()):
            channel_posts = sorted(today_by_project[proj], key=lambda m: m.channel)
            links = " · ".join(f"<{m.url}|{m.channel}>" for m in channel_posts)
            lines.append(f"• {proj} → {links}")

    return {"text": "\n".join(lines)}


def _engaged_line(m: PostMetrics) -> str:
    """One per-post line in the 'What got engagement' section.

    Format: `• project → channel · N eng (breakdown) [· Nv] · <url|open>`

    - Breakdown uses L/R/C for likes/reposts/replies, only non-zero components.
    - Views suffix only if views > 0 (most platforms don't report views publicly).
    - Link text is 'open' rather than the long URL for scannability.
    """
    counts: list[str] = []
    if m.likes:
        counts.append(f"{m.likes}L")
    if m.reposts:
        counts.append(f"{m.reposts}R")
    if m.replies:
        counts.append(f"{m.replies}C")
    breakdown = " ".join(counts)

    views_suffix = f" · {m.views}v" if m.views else ""
    return (
        f"• *{m.project}* → {m.channel} · "
        f"{m.engagement} eng ({breakdown}){views_suffix} · "
        f"<{m.url}|open>"
    )


def _failing_line(m: PostMetrics) -> str:
    """One per-post line in the 'Can't fetch metrics' section.

    Classifies the error into a short tag so the cause is scannable:
      - post-not-found → the platform doesn't recognize the URL (likely removed)
      - no-fetcher     → the pipeline doesn't support metrics for this channel
      - other          → first part of the raw error string
    """
    err = (m.error or "").strip()
    low = err.lower()
    if "not found" in low:
        tag = "post-not-found"
    elif "no metrics fetcher" in low:
        tag = "no-fetcher"
    else:
        tag = err[:40]

    posted = f" · posted {m.posted_at[5:]}" if m.posted_at else ""
    return (
        f"• {m.channel} · *{m.project}* · "
        f"`{tag}`{posted} · "
        f"<{m.url}|open>"
    )


def send_slack(payload: dict, webhook_url: str) -> bool:
    """Send a report to Slack via incoming webhook."""
    import httpx

    try:
        resp = httpx.post(webhook_url, json=payload, timeout=10)
        return resp.status_code == 200
    except Exception:
        return False
