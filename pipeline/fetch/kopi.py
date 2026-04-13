"""Fetch top-scoring email designs from Kopi AI for Pinterest posting.

Calls the Kopi gallery API, filters for exported emails above a score
threshold, and excludes emails already in the posted manifest.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from pipeline.report import load_manifest


@dataclass
class KopiEmail:
    chat_id: str
    title: str
    subject_line: str
    screenshot_url: str
    email_url: str
    score: float


def fetch_top_emails(
    api_url: str,
    brand_id: str | None = None,
    limit: int = 5,
    min_score: float = 70,
) -> list[KopiEmail]:
    """Fetch top-scoring exported emails from Kopi, excluding already-posted ones.

    Args:
        api_url: Base API URL (e.g., "https://trykopi.ai/api")
        brand_id: Optional brand filter
        limit: Max emails to return
        min_score: Minimum critique score threshold
    """
    params: dict = {"limit": limit, "minScore": min_score, "exported": "true"}
    if brand_id:
        params["brandId"] = brand_id

    resp = httpx.get(
        f"{api_url}/emails/gallery",
        params=params,
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    # Parse response
    emails = []
    for item in data:
        emails.append(KopiEmail(
            chat_id=item["chatId"],
            title=item.get("title", ""),
            subject_line=item.get("subjectLine", ""),
            screenshot_url=item["screenshotUrl"],
            email_url=item.get("emailUrl", f"https://trykopi.ai/p/{item['chatId']}"),
            score=item.get("critiqueScore", 0),
        ))

    # Filter out already-posted emails (don't double dip)
    manifest = load_manifest()
    posted_urls = {entry.get("url", "") for entry in manifest}
    posted_ids = set()
    for url in posted_urls:
        # Extract chatId from trykopi.ai/p/{chatId} URLs
        if "/p/" in url:
            posted_ids.add(url.split("/p/")[-1].split("/")[0].split("?")[0])

    return [e for e in emails if e.chat_id not in posted_ids]
