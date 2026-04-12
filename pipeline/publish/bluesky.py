"""Bluesky publisher via AT Protocol.

Auth: app password -> session JWT. Posts via com.atproto.repo.createRecord.
Rate limit: ~1,666 creates/hr (5,000 pts/hr at 3 pts per create).
Bot policy: label account as automated, no unsolicited interactions.
"""

from __future__ import annotations

from dataclasses import dataclass

from atproto import Client

from pipeline.config import Config
from pipeline.publish import PostResult


@dataclass
class BlueskyPublisher:
    channel: str = "bluesky"

    def publish(self, draft: str, config: Config) -> PostResult:
        creds = config.require_bluesky()

        if config.dry_run:
            return PostResult(
                url=None,
                channel=self.channel,
                success=True,
                error="[dry run] would post to Bluesky",
            )

        try:
            client = Client()
            client.login(creds.handle, creds.app_password)
            response = client.send_post(text=draft)

            # Build the post URL from the response.
            # response.uri is like at://did:plc:.../app.bsky.feed.post/...
            uri = response.uri
            rkey = uri.split("/")[-1]
            url = f"https://bsky.app/profile/{creds.handle}/post/{rkey}"

            return PostResult(url=url, channel=self.channel, success=True)

        except Exception as e:
            return PostResult(
                url=None,
                channel=self.channel,
                success=False,
                error=str(e),
            )
