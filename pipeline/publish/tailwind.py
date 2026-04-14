"""Pinterest publisher via Tailwind API.

Tailwind is a Pinterest API partner since 2012 with Standard access.
Posting through Tailwind's API bypasses Pinterest's own approval process —
pins publish under Tailwind's approved connection.

Auth: Bearer API key from Settings > API Access in Tailwind.
Endpoint: POST https://api-v1.tailwind.ai/v1/accounts/{accountId}/posts
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC

import httpx

from pipeline.config import Config
from pipeline.publish import PostResult

TAILWIND_API_URL = "https://api-v1.tailwind.ai/v1"


@dataclass
class TailwindPublisher:
    channel: str = "pinterest"  # Tailwind publishes TO Pinterest

    def publish(
        self,
        draft: str,
        config: Config,
        image_url: str | None = None,
        image_alt: str | None = None,
        title: str | None = None,
        link: str | None = None,
        send_at: str | None = None,
        **kwargs,
    ) -> PostResult:
        api_key = os.environ.get("TAILWIND_API_KEY")
        account_id = os.environ.get("TAILWIND_ACCOUNT_ID")
        board_id = os.environ.get("TAILWIND_BOARD_ID")

        if not (api_key and account_id and board_id):
            return PostResult(
                url=None,
                channel=self.channel,
                success=False,
                error="TAILWIND_API_KEY, TAILWIND_ACCOUNT_ID, and TAILWIND_BOARD_ID required",
            )

        if not image_url:
            return PostResult(
                url=None,
                channel=self.channel,
                success=False,
                error="Pinterest requires an image_url",
            )

        if config.dry_run:
            return PostResult(
                url=None,
                channel=self.channel,
                success=True,
                error=f"[dry run] would pin via Tailwind: {title or draft[:50]}",
            )

        # Default to publishing ~1 minute from now (Tailwind requires future timestamp)
        if send_at is None:
            from datetime import datetime, timedelta
            send_at = (datetime.now(UTC) + timedelta(minutes=1)).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )

        payload: dict = {
            "mediaUrl": image_url,
            "mediaType": "image",
            "title": (title or draft[:100])[:100],
            "description": draft[:500],
            "boardId": board_id,
            "sendAt": send_at,
        }
        if link:
            payload["url"] = link
        if image_alt:
            payload["altText"] = image_alt[:500]

        try:
            resp = httpx.post(
                f"{TAILWIND_API_URL}/accounts/{account_id}/posts",
                json=payload,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

            post_data = data.get("data", {}).get("post", {})
            post_id = post_data.get("id", "")
            pin_id = post_data.get("pinId", "")

            if pin_id:
                url = f"https://www.pinterest.com/pin/{pin_id}/"
            elif post_id:
                url = f"https://www.tailwindapp.com/posts/{post_id}"
            else:
                url = None

            return PostResult(url=url, channel=self.channel, success=True)

        except Exception as e:
            return PostResult(
                url=None,
                channel=self.channel,
                success=False,
                error=str(e),
            )
