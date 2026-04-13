"""Fetch top-scoring email designs from Kopi AI for image posting.

Calls the Kopi gallery API (GET /api/emails/gallery), which returns
public emails with critiqueScore >= 80, sorted by score.
Excludes emails already in the posted manifest to avoid re-posting.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from pipeline.report import load_manifest


@dataclass
class KopiEmail:
    id: str
    title: str
    brand_name: str | None
    screenshot_url: str
    email_url: str
    score: int | None
    slug: str


def fetch_top_emails(
    base_url: str,
    limit: int = 10,
    sort_by: str = "critiqueScore",
) -> list[KopiEmail]:
    """Fetch top-scoring public emails from Kopi, excluding already-posted ones.

    Args:
        base_url: Kopi base URL (e.g., "https://trykopi.ai")
        limit: Max emails to return
        sort_by: "critiqueScore" or "createdAt"
    """
    resp = httpx.get(
        f"{base_url}/api/emails/gallery",
        params={"limit": limit, "sortBy": sort_by, "sortOrder": "desc"},
        timeout=15,
        follow_redirects=True,
    )
    resp.raise_for_status()
    data = resp.json()

    emails = []
    for item in data.get("data", []):
        screenshot = item.get("screenshotUrl")
        if not screenshot:
            continue
        slug = item.get("slug", item["id"])
        emails.append(KopiEmail(
            id=item["id"],
            title=item.get("title", ""),
            brand_name=item.get("brandName"),
            screenshot_url=screenshot,
            email_url=f"{base_url}/emails/{slug}",
            score=item.get("critiqueScore"),
            slug=slug,
        ))

    # Filter out already-posted emails by source_id (don't double dip)
    manifest = load_manifest()
    posted_source_ids = {entry.get("source_id", "") for entry in manifest}

    return [e for e in emails if f"kopi:{e.id}" not in posted_source_ids]
