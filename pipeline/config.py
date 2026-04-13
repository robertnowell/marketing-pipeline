"""Credential and configuration loading from environment variables.

Every secret lives in an env var. The Config dataclass validates that required
credentials are present for the requested operation, so the caller gets a clear
error instead of a mid-publish KeyError.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root if present
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)


@dataclass(frozen=True)
class BlueskyConfig:
    handle: str
    app_password: str


@dataclass(frozen=True)
class DevtoConfig:
    api_key: str


@dataclass(frozen=True)
class HashnodeConfig:
    pat: str
    publication_id: str


@dataclass(frozen=True)
class MastodonConfig:
    access_token: str
    instance_url: str  # e.g. "https://hachyderm.io"


@dataclass(frozen=True)
class PinterestConfig:
    access_token: str
    board_id: str


@dataclass
class Config:
    """Pipeline configuration loaded from environment variables.

    All fields are optional at construction time — only validated when a
    specific operation needs them (draft needs anthropic_api_key, publish
    needs the relevant channel config, etc.).
    """

    anthropic_api_key: str | None = None
    bluesky: BlueskyConfig | None = None
    devto: DevtoConfig | None = None
    hashnode: HashnodeConfig | None = None
    mastodon: MastodonConfig | None = None
    pinterest: PinterestConfig | None = None

    # Operational flags
    dry_run: bool = False

    @classmethod
    def from_env(cls) -> Config:
        """Load all available credentials from environment variables."""
        bluesky = None
        if os.environ.get("BLUESKY_HANDLE") and os.environ.get("BLUESKY_APP_PASSWORD"):
            bluesky = BlueskyConfig(
                handle=os.environ["BLUESKY_HANDLE"],
                app_password=os.environ["BLUESKY_APP_PASSWORD"],
            )

        devto = None
        if os.environ.get("DEVTO_API_KEY"):
            devto = DevtoConfig(api_key=os.environ["DEVTO_API_KEY"])

        hashnode = None
        if os.environ.get("HASHNODE_PAT") and os.environ.get("HASHNODE_PUBLICATION_ID"):
            hashnode = HashnodeConfig(
                pat=os.environ["HASHNODE_PAT"],
                publication_id=os.environ["HASHNODE_PUBLICATION_ID"],
            )

        mastodon = None
        if os.environ.get("MASTODON_ACCESS_TOKEN") and os.environ.get("MASTODON_INSTANCE_URL"):
            mastodon = MastodonConfig(
                access_token=os.environ["MASTODON_ACCESS_TOKEN"],
                instance_url=os.environ["MASTODON_INSTANCE_URL"].rstrip("/"),
            )

        pinterest = None
        if os.environ.get("PINTEREST_ACCESS_TOKEN") and os.environ.get("PINTEREST_BOARD_ID"):
            pinterest = PinterestConfig(
                access_token=os.environ["PINTEREST_ACCESS_TOKEN"],
                board_id=os.environ["PINTEREST_BOARD_ID"],
            )

        return cls(
            anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY"),
            bluesky=bluesky,
            devto=devto,
            hashnode=hashnode,
            mastodon=mastodon,
            pinterest=pinterest,
        )

    def require_anthropic(self) -> str:
        if not self.anthropic_api_key:
            raise ConfigError("ANTHROPIC_API_KEY is required for drafting")
        return self.anthropic_api_key

    def require_bluesky(self) -> BlueskyConfig:
        if not self.bluesky:
            raise ConfigError("BLUESKY_HANDLE and BLUESKY_APP_PASSWORD are required")
        return self.bluesky

    def require_devto(self) -> DevtoConfig:
        if not self.devto:
            raise ConfigError("DEVTO_API_KEY is required")
        return self.devto

    def require_hashnode(self) -> HashnodeConfig:
        if not self.hashnode:
            raise ConfigError("HASHNODE_PAT and HASHNODE_PUBLICATION_ID are required")
        return self.hashnode

    def require_mastodon(self) -> MastodonConfig:
        if not self.mastodon:
            raise ConfigError(
                "MASTODON_ACCESS_TOKEN and MASTODON_INSTANCE_URL are required"
            )
        return self.mastodon

    def require_pinterest(self) -> PinterestConfig:
        if not self.pinterest:
            raise ConfigError(
                "PINTEREST_ACCESS_TOKEN and PINTEREST_BOARD_ID are required"
            )
        return self.pinterest


class ConfigError(Exception):
    """Raised when a required credential is missing."""
