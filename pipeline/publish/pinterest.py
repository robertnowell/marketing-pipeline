"""Pinterest publisher — posts pins with images.

Auth: OAuth 2.0 access token with pins:write scope.
Endpoint: POST /pins via pinterest-api-sdk.
Designed for visual content: email designs, screenshots, product images.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from pipeline.config import Config
from pipeline.publish import PostResult


@dataclass
class PinterestPublisher:
    channel: str = "pinterest"

    def publish(
        self,
        draft: str,
        config: Config,
        image_url: str | None = None,
        link: str | None = None,
        title: str | None = None,
    ) -> PostResult:
        creds = config.require_pinterest()

        if config.dry_run:
            return PostResult(
                url=None,
                channel=self.channel,
                success=True,
                error=f"[dry run] would pin: {title or draft[:50]}",
            )

        if not image_url:
            return PostResult(
                url=None,
                channel=self.channel,
                success=False,
                error="Pinterest requires an image_url",
            )

        try:
            # Use the Pinterest API v5 directly via httpx
            # (avoids pulling in the full SDK as a dependency)
            payload: dict = {
                "board_id": creds.board_id,
                "media_source": {
                    "source_type": "image_url",
                    "url": image_url,
                },
            }
            if title:
                payload["title"] = title[:100]  # Pinterest title limit
            if draft:
                payload["description"] = draft[:500]  # Pinterest description limit
            if link:
                payload["link"] = link

            import os
            api_url = os.environ.get("PINTEREST_API_URL", "https://api.pinterest.com")
            resp = httpx.post(
                f"{api_url}/v5/pins",
                json=payload,
                headers={
                    "Authorization": f"Bearer {creds.access_token}",
                    "Content-Type": "application/json",
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

            pin_id = data.get("id", "")
            pin_url = f"https://www.pinterest.com/pin/{pin_id}/" if pin_id else None

            return PostResult(url=pin_url, channel=self.channel, success=True)

        except Exception as e:
            return PostResult(
                url=None,
                channel=self.channel,
                success=False,
                error=str(e),
            )
