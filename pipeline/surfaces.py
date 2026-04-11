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
        kind = self._kinds.get(project.kind, {}) or {}

        # 1. Build directories: audience base + kind additives.
        dir_map: dict[str, Directory] = {}

        for entry in audience.get("directories", []) or []:
            d = _coerce_directory(entry, dir_map)
            if d is not None:
                dir_map[d.name] = d

        for entry in kind.get("directories_additive", []) or []:
            d = _coerce_directory(entry, dir_map)
            if d is not None:
                dir_map[d.name] = d

        # 2. Forums: audience manual + kind additives.
        forums_seen: set[str] = set()
        forums: list[str] = []
        for f in (audience.get("forums_manual") or []) + (kind.get("forums_additive") or []):
            if f not in forums_seen:
                forums_seen.add(f)
                forums.append(f)

        return ResolvedSurfaces(
            daily_social=list(audience.get("daily_social") or []),
            content_blogs=list(audience.get("content_blogs") or []),
            directories=list(dir_map.values()),
            forums_manual=forums,
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
