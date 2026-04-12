"""Mastodon publisher via REST API.

Auth: OAuth 2.0 bearer token (write:statuses scope).
Endpoint: POST /api/v1/statuses on the instance host.
Rate limit: 300 req/5min (instance-variable).
Bot policy: set "automated account" flag in profile settings.
"""

from __future__ import annotations

from dataclasses import dataclass

from mastodon import Mastodon

from pipeline.config import Config
from pipeline.publish import PostResult


@dataclass
class MastodonPublisher:
    channel: str = "mastodon"

    def publish(self, draft: str, config: Config) -> PostResult:
        creds = config.require_mastodon()

        if config.dry_run:
            return PostResult(
                url=None,
                channel=self.channel,
                success=True,
                error="[dry run] would post to Mastodon",
            )

        try:
            client = Mastodon(
                access_token=creds.access_token,
                api_base_url=creds.instance_url,
            )
            status = client.status_post(draft)
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
