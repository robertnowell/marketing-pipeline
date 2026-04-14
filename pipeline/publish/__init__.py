"""Channel publishers — common interface and registry.

Each publisher takes a draft string + config and returns a PostResult.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from pipeline.config import Config


@dataclass
class PostResult:
    url: str | None
    channel: str
    success: bool
    error: str | None = None


class Publisher(Protocol):
    """Interface that every channel publisher implements."""

    channel: str

    def publish(self, draft: str, config: Config) -> PostResult: ...


def get_publisher(channel: str) -> Publisher:
    """Return the publisher for a given channel name."""
    import os

    from pipeline.publish.bluesky import BlueskyPublisher
    from pipeline.publish.devto import DevtoPublisher
    from pipeline.publish.hashnode import HashnodePublisher
    from pipeline.publish.mastodon import MastodonPublisher
    from pipeline.publish.pinterest import PinterestPublisher
    from pipeline.publish.tailwind import TailwindPublisher

    # Route Pinterest via Tailwind if TAILWIND_API_KEY is set,
    # otherwise use direct Pinterest API.
    pinterest_pub: Publisher = (
        TailwindPublisher() if os.environ.get("TAILWIND_API_KEY") else PinterestPublisher()
    )

    publishers: dict[str, Publisher] = {
        "bluesky": BlueskyPublisher(),
        "devto": DevtoPublisher(),
        "hashnode": HashnodePublisher(),
        "mastodon": MastodonPublisher(),
        "pinterest": pinterest_pub,
    }
    publisher = publishers.get(channel.lower())
    if publisher is None:
        raise ValueError(
            f"No publisher for channel '{channel}'. "
            f"Available: {', '.join(publishers.keys())}"
        )
    return publisher
