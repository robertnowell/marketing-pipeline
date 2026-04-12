"""Config loading and validation tests."""

from __future__ import annotations

import pytest

from pipeline.config import BlueskyConfig, Config, ConfigError


def test_from_env_loads_all_creds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("BLUESKY_HANDLE", "test.bsky.social")
    monkeypatch.setenv("BLUESKY_APP_PASSWORD", "app-pw")
    monkeypatch.setenv("DEVTO_API_KEY", "devto-key")
    monkeypatch.setenv("HASHNODE_PAT", "hn-pat")
    monkeypatch.setenv("HASHNODE_PUBLICATION_ID", "pub-123")
    monkeypatch.setenv("MASTODON_ACCESS_TOKEN", "masto-token")
    monkeypatch.setenv("MASTODON_INSTANCE_URL", "https://hachyderm.io/")

    config = Config.from_env()
    assert config.anthropic_api_key == "sk-test"
    assert config.bluesky is not None
    assert config.bluesky.handle == "test.bsky.social"
    assert config.devto is not None
    assert config.hashnode is not None
    assert config.hashnode.publication_id == "pub-123"
    assert config.mastodon is not None
    assert config.mastodon.instance_url == "https://hachyderm.io"  # trailing slash stripped


def test_from_env_missing_creds(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing env vars produce None, not errors — errors come from require_*."""
    for key in [
        "ANTHROPIC_API_KEY", "BLUESKY_HANDLE", "BLUESKY_APP_PASSWORD",
        "DEVTO_API_KEY", "HASHNODE_PAT", "HASHNODE_PUBLICATION_ID",
        "MASTODON_ACCESS_TOKEN", "MASTODON_INSTANCE_URL",
    ]:
        monkeypatch.delenv(key, raising=False)

    config = Config.from_env()
    assert config.anthropic_api_key is None
    assert config.bluesky is None
    assert config.devto is None
    assert config.hashnode is None
    assert config.mastodon is None


def test_require_anthropic_raises_when_missing() -> None:
    config = Config()
    with pytest.raises(ConfigError, match="ANTHROPIC_API_KEY"):
        config.require_anthropic()


def test_require_bluesky_raises_when_missing() -> None:
    config = Config()
    with pytest.raises(ConfigError, match="BLUESKY"):
        config.require_bluesky()


def test_require_devto_raises_when_missing() -> None:
    config = Config()
    with pytest.raises(ConfigError, match="DEVTO"):
        config.require_devto()


def test_require_hashnode_raises_when_missing() -> None:
    config = Config()
    with pytest.raises(ConfigError, match="HASHNODE"):
        config.require_hashnode()


def test_require_mastodon_raises_when_missing() -> None:
    config = Config()
    with pytest.raises(ConfigError, match="MASTODON"):
        config.require_mastodon()


def test_require_returns_value_when_present() -> None:
    config = Config(
        anthropic_api_key="key",
        bluesky=BlueskyConfig(handle="h", app_password="p"),
    )
    assert config.require_anthropic() == "key"
    assert config.require_bluesky().handle == "h"


def test_partial_bluesky_creds_not_loaded(monkeypatch: pytest.MonkeyPatch) -> None:
    """If only BLUESKY_HANDLE is set but not APP_PASSWORD, bluesky should be None."""
    monkeypatch.setenv("BLUESKY_HANDLE", "test.bsky.social")
    monkeypatch.delenv("BLUESKY_APP_PASSWORD", raising=False)
    config = Config.from_env()
    assert config.bluesky is None
