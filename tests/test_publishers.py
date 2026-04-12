"""Publisher tests — verify dry-run behavior and interface compliance."""

from __future__ import annotations

import pytest

from pipeline.config import BlueskyConfig, Config, DevtoConfig, HashnodeConfig, MastodonConfig
from pipeline.publish import get_publisher
from pipeline.publish.bluesky import BlueskyPublisher
from pipeline.publish.devto import DevtoPublisher
from pipeline.publish.hashnode import HashnodePublisher
from pipeline.publish.mastodon import MastodonPublisher


def _dry_config() -> Config:
    """Config with all creds present but dry_run=True."""
    return Config(
        anthropic_api_key="sk-test",
        bluesky=BlueskyConfig(handle="test.bsky.social", app_password="pw"),
        devto=DevtoConfig(api_key="devto-key"),
        hashnode=HashnodeConfig(pat="hn-pat", publication_id="pub-123"),
        mastodon=MastodonConfig(access_token="masto-tok", instance_url="https://mastodon.social"),
        dry_run=True,
    )


def test_bluesky_dry_run() -> None:
    publisher = BlueskyPublisher()
    result = publisher.publish("test draft", _dry_config())
    assert result.success
    assert result.channel == "bluesky"
    assert "dry run" in result.error


def test_devto_dry_run() -> None:
    publisher = DevtoPublisher()
    result = publisher.publish("test draft", _dry_config())
    assert result.success
    assert result.channel == "devto"
    assert "dry run" in result.error


def test_hashnode_dry_run() -> None:
    publisher = HashnodePublisher()
    result = publisher.publish("test draft", _dry_config())
    assert result.success
    assert result.channel == "hashnode"
    assert "dry run" in result.error


def test_mastodon_dry_run() -> None:
    publisher = MastodonPublisher()
    result = publisher.publish("test draft", _dry_config())
    assert result.success
    assert result.channel == "mastodon"
    assert "dry run" in result.error


def test_get_publisher_returns_correct_types() -> None:
    assert isinstance(get_publisher("bluesky"), BlueskyPublisher)
    assert isinstance(get_publisher("devto"), DevtoPublisher)
    assert isinstance(get_publisher("hashnode"), HashnodePublisher)
    assert isinstance(get_publisher("mastodon"), MastodonPublisher)


def test_get_publisher_case_insensitive() -> None:
    assert isinstance(get_publisher("Bluesky"), BlueskyPublisher)
    assert isinstance(get_publisher("DEVTO"), DevtoPublisher)


def test_get_publisher_unknown_raises() -> None:
    with pytest.raises(ValueError, match="No publisher for channel"):
        get_publisher("twitter")


def test_all_publishers_have_channel_attr() -> None:
    for name in ["bluesky", "devto", "hashnode", "mastodon"]:
        pub = get_publisher(name)
        assert pub.channel == name


def test_bluesky_missing_creds_raises() -> None:
    config = Config(dry_run=False)
    publisher = BlueskyPublisher()
    # Should raise ConfigError, not crash with AttributeError
    from pipeline.config import ConfigError
    with pytest.raises(ConfigError):
        publisher.publish("test", config)


def test_mastodon_missing_creds_raises() -> None:
    config = Config(dry_run=False)
    publisher = MastodonPublisher()
    from pipeline.config import ConfigError
    with pytest.raises(ConfigError):
        publisher.publish("test", config)
