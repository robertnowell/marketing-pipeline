"""Resolve a project to its effective channel + directory set.

The resolver is the piece that makes the pipeline work for a Shopify tool and a
Claude Code plugin with the same code. `audience` selects which social surfaces
and directories apply; `kind` layers on any additive directories specific to the
project type.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

from pipeline.registry import Project

_yaml = YAML()


@dataclass
class Directory:
    name: str
    type: str  # pr | cli | form | contact
    repo: str | None = None
    url: str | None = None
    tool: str | None = None
    contact: str | None = None


@dataclass
class ResolvedSurfaces:
    daily_social: list[str] = field(default_factory=list)
    content_blogs: list[str] = field(default_factory=list)
    directories: list[Directory] = field(default_factory=list)
    forums_manual: list[str] = field(default_factory=list)
    # Watering holes: read-only listener targets for pain-catalog harvesting.
    # Each entry is a dict with a `type` discriminator (hn_algolia, reddit_search,
    # github_issues, bluesky_search, so_tag, ...) plus type-specific fields.
    # Passed through as raw dicts; safari.py / listener.py dispatch on `type`.
    watering_holes: list[dict] = field(default_factory=list)

    @property
    def daily_channels(self) -> list[str]:
        """All channels the daily loop should consider for this project."""
        # Preserve order, dedupe.
        seen: set[str] = set()
        result: list[str] = []
        for channel in self.daily_social + self.content_blogs:
            if channel not in seen:
                seen.add(channel)
                result.append(channel)
        return result


class SurfaceRegistry:
    def __init__(self, data: dict[str, Any]) -> None:
        self._audiences: dict[str, Any] = data.get("audiences", {}) or {}
        self._kinds: dict[str, Any] = data.get("kinds", {}) or {}

    @classmethod
    def load(cls, path: Path | str = "surfaces.yml") -> SurfaceRegistry:
        raw = _yaml.load(Path(path).read_text())
        return cls(raw or {})

    def resolve(self, project: Project) -> ResolvedSurfaces:
        audience = self._audiences.get(project.audience)
        if audience is None:
            raise KeyError(
                f"audience '{project.audience}' for project not found in surfaces.yml"
            )

        # Support comma-separated kinds (e.g., "mcp-server,claude-skill")
        kind_names = [k.strip() for k in project.kind.split(",")]
        kinds = [self._kinds.get(k, {}) or {} for k in kind_names]

        # 1. Build directories: audience base + ALL kind additives.
        dir_map: dict[str, Directory] = {}

        for entry in audience.get("directories", []) or []:
            d = _coerce_directory(entry, dir_map)
            if d is not None:
                dir_map[d.name] = d

        for kind in kinds:
            for entry in kind.get("directories_additive", []) or []:
                d = _coerce_directory(entry, dir_map)
                if d is not None:
                    dir_map[d.name] = d

        # 2. Forums: audience manual + ALL kind additives.
        forums_seen: set[str] = set()
        forums: list[str] = []
        all_forums = list(audience.get("forums_manual") or [])
        for kind in kinds:
            all_forums.extend(kind.get("forums_additive") or [])
        for f in all_forums:
            if f not in forums_seen:
                forums_seen.add(f)
                forums.append(f)

        return ResolvedSurfaces(
            daily_social=list(audience.get("daily_social") or []),
            content_blogs=list(audience.get("content_blogs") or []),
            directories=list(dir_map.values()),
            forums_manual=forums,
            # Watering holes are audience-only in MVP. No kind-layering — kinds
            # currently only layer directories. Revisit if a kind ever needs
            # to add type-specific listener targets.
            watering_holes=list(audience.get("watering_holes") or []),
        )


def _coerce_directory(entry: Any, existing: dict[str, Directory]) -> Directory | None:
    """Accept either a dict or a string reference to an already-seen directory."""
    if isinstance(entry, str):
        # String reference — look up an earlier entry by name.
        return existing.get(entry)
    if isinstance(entry, dict):
        return Directory(
            name=entry["name"],
            type=entry.get("type", "form"),
            repo=entry.get("repo"),
            url=entry.get("url"),
            tool=entry.get("tool"),
            contact=entry.get("contact"),
        )
    return None
