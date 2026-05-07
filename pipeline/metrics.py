"""Fetch engagement metrics from each platform for posted content.

Each platform has a public or authenticated API that returns likes, reposts,
comments, and views for a given post URL.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta

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


def fetch_bluesky_metrics(post: dict, config: Config) -> dict:
    """Fetch metrics for a Bluesky post. Public API, no auth needed."""
    url = post["url"]
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


def fetch_devto_metrics(post: dict, config: Config) -> dict:
    """Fetch metrics for a Dev.to article. Uses API key for view counts."""
    # Extract article slug from URL
    # URL format: https://dev.to/{username}/{slug}
    url = post["url"]
    try:
        creds = config.require_devto()
        # Paginate through user's articles. Dev.to defaults per_page=30, caps
        # at 1000; stop once we find the URL or the page is short.
        for page in range(1, 11):
            resp = httpx.get(
                "https://dev.to/api/articles/me/published",
                params={"page": page, "per_page": 100},
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
            if len(articles) < 100:
                break

        return {"error": f"Article not found in your published list: {url}"}
    except Exception as e:
        return {"error": str(e)}


def fetch_mastodon_metrics(post: dict, config: Config) -> dict:
    """Fetch metrics for a Mastodon status."""
    url = post["url"]
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


_HASHNODE_BY_ID_QUERY = """
query GetPostById($id: ID!) {
  post(id: $id) {
    views
    reactionCount
    responseCount
  }
}
"""

_HASHNODE_BY_SLUG_QUERY = """
query GetPostBySlug($slug: String!, $host: String!) {
  publication(host: $host) {
    post(slug: $slug) {
      views
      reactionCount
      responseCount
    }
  }
}
"""


def fetch_hashnode_metrics(post: dict, config: Config) -> dict:
    """Fetch metrics for a Hashnode post via GraphQL.

    Hashnode rewrites slugs after edits, so the URL stored at publish time may
    no longer resolve via the publication+slug query. We prefer the stable
    `post_id` (returned by `publishDraft` and persisted in the manifest), and
    fall back to slug for old manifest entries that predate post_id capture.
    """
    url = post["url"]
    post_id = post.get("post_id")
    try:
        creds = config.require_hashnode()

        if post_id:
            resp = httpx.post(
                "https://gql.hashnode.com",
                json={"query": _HASHNODE_BY_ID_QUERY, "variables": {"id": post_id}},
                headers={"Authorization": creds.pat},
                timeout=15,
            )
            resp.raise_for_status()
            node = resp.json().get("data", {}).get("post")
            if not node:
                return {"error": f"Post not found by id {post_id}: {url}"}
            return {
                "likes": node.get("reactionCount", 0),
                "replies": node.get("responseCount", 0),
                "views": node.get("views", 0),
            }

        # Legacy fallback: pre–post_id manifest entries.
        slug = url.rstrip("/").split("/")[-1]
        host = url.split("/")[2]
        resp = httpx.post(
            "https://gql.hashnode.com",
            json={
                "query": _HASHNODE_BY_SLUG_QUERY,
                "variables": {"slug": slug, "host": host},
            },
            headers={"Authorization": creds.pat},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        node = data.get("data", {}).get("publication", {}).get("post")
        if not node:
            return {"error": f"Post not found (slug may have been rewritten): {url}"}

        return {
            "likes": node.get("reactionCount", 0),
            "replies": node.get("responseCount", 0),
            "views": node.get("views", 0),
        }
    except Exception as e:
        return {"error": str(e)}


def fetch_pinterest_metrics(post: dict, config: Config) -> dict:
    """Fetch metrics for a Pinterest pin via Pinterest API v5.

    Mapping (Pinterest → PostMetrics):
      SAVE           → likes    (a save is the user-saving-for-later signal)
      OUTBOUND_CLICK → reposts  (highest-intent propagation off-platform)
      PIN_CLICK      → replies  (engagement depth — expanded the pin)
      IMPRESSION     → views

    Tailwind staging URLs (https://www.tailwindapp.com/posts/...) belong to
    pins that hadn't yet rolled to Pinterest when the manifest entry was
    written. They have no Pinterest pin_id and no analytics; surface that
    explicitly so the daily digest tags them usefully instead of `no-fetcher`.
    """
    url = post["url"]
    pin_id = post.get("post_id")

    if "tailwindapp.com" in url and not pin_id:
        return {"error": "Tailwind staging URL — pin not yet on Pinterest"}

    if not pin_id:
        match = re.match(r"https://(?:www\.)?pinterest\.com/pin/(\d+)/?", url)
        if not match:
            return {"error": f"Can't parse Pinterest URL: {url}"}
        pin_id = match.group(1)

    try:
        creds = config.require_pinterest()
        end = datetime.utcnow().date()
        start = end - timedelta(days=89)  # Pinterest caps the window at 90 days
        resp = httpx.get(
            f"https://api.pinterest.com/v5/pins/{pin_id}/analytics",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "metric_types": "IMPRESSION,SAVE,OUTBOUND_CLICK,PIN_CLICK",
            },
            headers={"Authorization": f"Bearer {creds.access_token}"},
            timeout=15,
        )
        if resp.status_code == 404:
            return {"error": f"Post not found: {url}"}
        resp.raise_for_status()
        summary = resp.json().get("all", {}).get("summary_metrics", {})

        return {
            "likes": int(summary.get("SAVE", 0)),
            "reposts": int(summary.get("OUTBOUND_CLICK", 0)),
            "replies": int(summary.get("PIN_CLICK", 0)),
            "views": int(summary.get("IMPRESSION", 0)),
        }
    except Exception as e:
        return {"error": str(e)}


FETCHERS = {
    "bluesky": fetch_bluesky_metrics,
    "devto": fetch_devto_metrics,
    "mastodon": fetch_mastodon_metrics,
    "hashnode": fetch_hashnode_metrics,
    "pinterest": fetch_pinterest_metrics,
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

    result = fetcher(post, config)
    if "error" in result:
        metrics.error = result["error"]
    else:
        metrics.likes = result.get("likes", 0)
        metrics.reposts = result.get("reposts", 0)
        metrics.replies = result.get("replies", 0)
        metrics.views = result.get("views", 0)

    return metrics
