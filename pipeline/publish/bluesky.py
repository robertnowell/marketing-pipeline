"""Bluesky publisher via AT Protocol.

Auth: app password -> session JWT. Posts via com.atproto.repo.createRecord.
Supports text-only and text+image posts.
Rate limit: ~1,666 creates/hr (5,000 pts/hr at 3 pts per create).
Bot policy: label account as automated, no unsolicited interactions.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx
from atproto import Client

from pipeline.config import Config
from pipeline.publish import PostResult


@dataclass
class BlueskyPublisher:
    channel: str = "bluesky"

    def publish(
        self,
        draft: str,
        config: Config,
        image_url: str | None = None,
        image_alt: str | None = None,
        **kwargs,
    ) -> PostResult:
        creds = config.require_bluesky()

        if config.dry_run:
            img_note = " + image" if image_url else ""
            return PostResult(
                url=None,
                channel=self.channel,
                success=True,
                error=f"[dry run] would post to Bluesky{img_note}",
            )

        try:
            client = Client()
            client.login(creds.handle, creds.app_password)

            if image_url:
                # Download image (follow redirects), upload as blob, fix mime type
                img_resp = httpx.get(image_url, timeout=15, follow_redirects=True)
                img_data = img_resp.content
                content_type = img_resp.headers.get("content-type", "image/png")
                if ";" in content_type:
                    content_type = content_type.split(";")[0].strip()
                if not content_type.startswith("image/"):
                    content_type = "image/png"

                upload = client.upload_blob(img_data)
                upload.blob.mime_type = content_type  # SDK doesn't set this correctly

                images = [{"alt": image_alt or "", "image": upload.blob}]
                embed = {"$type": "app.bsky.embed.images", "images": images}
                response = client.send_post(text=draft, embed=embed)
            else:
                response = client.send_post(text=draft)

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
