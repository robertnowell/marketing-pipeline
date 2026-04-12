"""Fetch engagement metrics from each platform for posted content.

Each platform has a public or authenticated API that returns likes, reposts,
comments, and views for a given post URL.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

import httpx

from pipeline.config import Config


@dataclass
class PostMetrics:
    url: str
    channel: str
    project: str
    angle: str
    posted_at: str
    likes: int = 0
    reposts: int = 0
    replies: int = 0
    views: int = 0
    fetched_at: str = ""
    error: str | None = None

    @property
    def engagement(self) -> int:
        return self.likes + self.reposts + self.replies

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "channel": self.channel,
            "project": self.project,
            "angle": self.angle,
            "posted_at": self.posted_at,
            "likes": self.likes,
            "reposts": self.reposts,
            "replies": self.replies,
            "views": self.views,
            "engagement": self.engagement,
            "fetched_at": self.fetched_at,
            "error": self.error,
        }


def fetch_bluesky_metrics(url: str, config: Config) -> dict:
    """Fetch metrics for a Bluesky post. Public API, no auth needed."""
    # URL format: https://bsky.app/profile/{handle}/post/{rkey}
    match = re.match(r"https://bsky\.app/profile/([^/]+)/post/([^/]+)", url)
    if not match:
        return {"error": f"Can't parse Bluesky URL: {url}"}

    handle, rkey = match.groups()

    try:
        # Resolve handle to DID
        resp = httpx.get(
            "https://public.api.bsky.app/xrpc/com.atproto.identity.resolveHandle",
            params={"handle": handle},
            timeout=10,
        )
        resp.raise_for_status()
        did = resp.json()["did"]

        # Fetch post thread
        uri = f"at://{did}/app.bsky.feed.post/{rkey}"
        resp = httpx.get(
            "https://public.api.bsky.app/xrpc/app.bsky.feed.getPostThread",
            params={"uri": uri, "depth": 0},
            timeout=10,
        )
        resp.raise_for_status()
        post = resp.json()["thread"]["post"]

        return {
            "likes": post.get("likeCount", 0),
            "reposts": post.get("repostCount", 0),
            "replies": post.get("replyCount", 0),
        }
    except Exception as e:
        return {"error": str(e)}


def fetch_devto_metrics(url: str, config: Config) -> dict:
    """Fetch metrics for a Dev.to article. Uses API key for view counts."""
    # Extract article slug from URL
    # URL format: https://dev.to/{username}/{slug}
    try:
        creds = config.require_devto()
        # Fetch user's articles and find the matching one
        resp = httpx.get(
            "https://dev.to/api/articles/me/published",
            headers={
                "api-key": creds.api_key,
                "Accept": "application/vnd.forem.api-v1+json",
            },
            timeout=15,
        )
        resp.raise_for_status()
        articles = resp.json()

        for article in articles:
            if article.get("url") == url:
                return {
                    "likes": article.get("positive_reactions_count", 0),
                    "replies": article.get("comments_count", 0),
                    "views": article.get("page_views_count", 0),
                }

        return {"error": f"Article not found in your published list: {url}"}
    except Exception as e:
        return {"error": str(e)}


def fetch_mastodon_metrics(url: str, config: Config) -> dict:
    """Fetch metrics for a Mastodon status."""
    # URL format: https://{instance}/@{user}/{id}
    match = re.match(r"https://([^/]+)/@[^/]+/(\d+)", url)
    if not match:
        return {"error": f"Can't parse Mastodon URL: {url}"}

    instance, status_id = match.groups()

    try:
        creds = config.require_mastodon()
        resp = httpx.get(
            f"{creds.instance_url}/api/v1/statuses/{status_id}",
            headers={"Authorization": f"Bearer {creds.access_token}"},
            timeout=10,
        )
        resp.raise_for_status()
        status = resp.json()

        return {
            "likes": status.get("favourites_count", 0),
            "reposts": status.get("reblogs_count", 0),
            "replies": status.get("replies_count", 0),
        }
    except Exception as e:
        return {"error": str(e)}


def fetch_hashnode_metrics(url: str, config: Config) -> dict:
    """Fetch metrics for a Hashnode post via GraphQL."""
    # Extract slug from URL — format varies by publication
    try:
        slug = url.rstrip("/").split("/")[-1]
        creds = config.require_hashnode()

        query = """
        query GetPost($slug: String!, $host: String!) {
          publication(host: $host) {
            post(slug: $slug) {
              views
              reactionCount
              responseCount
            }
          }
        }
        """
        # Extract host from URL
        host = url.split("/")[2]

        resp = httpx.post(
            "https://gql.hashnode.com",
            json={
                "query": query,
                "variables": {"slug": slug, "host": host},
            },
            headers={"Authorization": creds.pat},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        post = data.get("data", {}).get("publication", {}).get("post")
        if not post:
            return {"error": f"Post not found: {url}"}

        return {
            "likes": post.get("reactionCount", 0),
            "replies": post.get("responseCount", 0),
            "views": post.get("views", 0),
        }
    except Exception as e:
        return {"error": str(e)}


FETCHERS = {
    "bluesky": fetch_bluesky_metrics,
    "devto": fetch_devto_metrics,
    "mastodon": fetch_mastodon_metrics,
    "hashnode": fetch_hashnode_metrics,
}


def fetch_metrics(post: dict, config: Config) -> PostMetrics:
    """Fetch metrics for a single posted item."""
    channel = post["channel"]
    fetcher = FETCHERS.get(channel)

    metrics = PostMetrics(
        url=post["url"],
        channel=channel,
        project=post["project"],
        angle=post.get("angle", ""),
        posted_at=post.get("posted_at", ""),
        fetched_at=datetime.utcnow().isoformat(timespec="seconds") + "Z",
    )

    if fetcher is None:
        metrics.error = f"No metrics fetcher for channel: {channel}"
        return metrics

    result = fetcher(post["url"], config)
    if "error" in result:
        metrics.error = result["error"]
    else:
        metrics.likes = result.get("likes", 0)
        metrics.reposts = result.get("reposts", 0)
        metrics.replies = result.get("replies", 0)
        metrics.views = result.get("views", 0)

    return metrics
