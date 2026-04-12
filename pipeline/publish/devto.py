"""Dev.to publisher via Forem v1 API.

Auth: API key header. Endpoint: POST https://dev.to/api/articles.
Rate limit: ~10 req/30s (undocumented for v1).
Content must be substantive, not primarily promotional.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from pipeline.config import Config
from pipeline.publish import PostResult

DEVTO_API_URL = "https://dev.to/api/articles"


@dataclass
class DevtoPublisher:
    channel: str = "devto"

    def publish(
        self,
        draft: str,
        config: Config,
        title: str | None = None,
        tags: list[str] | None = None,
        series: str | None = None,
        canonical_url: str | None = None,
    ) -> PostResult:
        creds = config.require_devto()

        if config.dry_run:
            return PostResult(
                url=None,
                channel=self.channel,
                success=True,
                error="[dry run] would post to Dev.to",
            )

        # Dev.to requires a title separate from the body.
        # If no title provided, extract from a '# Title' line or truncate first sentence.
        if title is None:
            first_line = draft.strip().split("\n", 1)[0]
            if first_line.startswith("# "):
                title = first_line.lstrip("# ").strip()
                draft = draft.strip().split("\n", 1)[1].strip() if "\n" in draft.strip() else draft
            else:
                # No title line — use first sentence, capped at 70 chars
                sentence = first_line.split(". ")[0].split(" — ")[0]
                title = sentence[:70].rstrip(" .,")
                # Keep full draft as body (don't strip the first line)

        article_data: dict = {
            "title": title,
            "body_markdown": draft,
            "published": True,
        }
        if tags:
            article_data["tags"] = tags[:4]  # Dev.to max 4 tags
        if series:
            article_data["series"] = series
        if canonical_url:
            article_data["canonical_url"] = canonical_url

        try:
            resp = httpx.post(
                DEVTO_API_URL,
                json={"article": article_data},
                headers={
                    "api-key": creds.api_key,
                    "Accept": "application/vnd.forem.api-v1+json",
                    "Content-Type": "application/json",
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            return PostResult(
                url=data.get("url"),
                channel=self.channel,
                success=True,
            )

        except Exception as e:
            return PostResult(
                url=None,
                channel=self.channel,
                success=False,
                error=str(e),
            )
