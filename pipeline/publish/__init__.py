"""Channel publishers — common interface and registry.

Each publisher takes a draft string + config and returns a PostResult.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Protocol

from pipeline.config import Config

# House style: no em-dashes (a classic AI tell). Strip them at the publish
# boundary so EVERY path — cycle, verbatim-approved, single — is covered here,
# once. Em-dash (U+2014) → comma; en-dashes (U+2013) are left alone so numeric
# ranges like "$3–5k" survive.
_EMDASH = re.compile(r"\s*—\s*")


def destyle(text: str | None) -> str | None:
    if not text:
        return text
    text = _EMDASH.sub(", ", text)
    text = re.sub(r",\s*,", ", ", text)   # collapse doubled commas the sub can create
    text = re.sub(r"\s+,", ",", text)     # tidy " ," → ","
    return text


@dataclass
class PostResult:
    url: str | None
    channel: str
    success: bool
    error: str | None = None
    # Platform's stable ID for this post (Hashnode post id, Pinterest pin id, etc.).
    # Stored in the manifest so metrics fetchers can query by ID instead of URL,
    # which protects against slug rewrites on platforms like Hashnode.
    post_id: str | None = None


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
    return _Destyled(publisher)


class _Destyled:
    """Wraps a publisher so all outgoing text is de-slopped (em-dashes stripped)
    at the single publish boundary — every call site is covered here, once."""

    def __init__(self, inner: Publisher):
        self._inner = inner
        self.channel = getattr(inner, "channel", None)

    def publish(self, draft: str, config: Config, **kwargs: Any) -> PostResult:
        if kwargs.get("title"):
            kwargs["title"] = destyle(kwargs["title"])
        return self._inner.publish(destyle(draft), config, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)
