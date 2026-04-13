"""Mastodon publisher via REST API.

Auth: OAuth 2.0 bearer token (write:statuses + write:media scopes).
Supports text-only and text+image posts.
Rate limit: 300 req/5min (instance-variable).
Bot policy: set "automated account" flag in profile settings.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx
from mastodon import Mastodon

from pipeline.config import Config
from pipeline.publish import PostResult


@dataclass
class MastodonPublisher:
    channel: str = "mastodon"

    def publish(
        self,
        draft: str,
        config: Config,
        image_url: str | None = None,
        image_alt: str | None = None,
        **kwargs,
    ) -> PostResult:
        creds = config.require_mastodon()

        if config.dry_run:
            img_note = " + image" if image_url else ""
            return PostResult(
                url=None,
                channel=self.channel,
                success=True,
                error=f"[dry run] would post to Mastodon{img_note}",
            )

        try:
            client = Mastodon(
                access_token=creds.access_token,
                api_base_url=creds.instance_url,
            )

            media_ids = []
            if image_url:
                # Download image and upload to Mastodon
                img_data = httpx.get(image_url, timeout=15).content
                media = client.media_post(img_data, mime_type="image/png", description=image_alt or "")
                media_ids.append(media["id"])

            status = client.status_post(draft, media_ids=media_ids or None)
            return PostResult(
                url=status.get("url"),
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
