"""Typed loader for projects.yml.

Pydantic validates; ruamel.yaml round-trips (preserves comments + ordering).
The cadence gate and rebalancer mutate projects.yml in place; the ruamel document
is the canonical representation, and the pydantic models are a validated snapshot.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field
from ruamel.yaml import YAML

_yaml = YAML()
_yaml.preserve_quotes = True
_yaml.indent(mapping=2, sequence=4, offset=2)


class Angle(BaseModel):
    id: str
    summary: str
    last_used: date | None = None


class ChannelWeight(BaseModel):
    weight: float = 1.0
    rolling_score: float = 0.0


class Project(BaseModel):
    repo: str  # GitHub repo URL or website URL (e.g., https://trykopi.ai)
    kind: str  # Comma-separated: "mcp-server,claude-skill", "saas-email-tool", etc.
    audience: str
    status: Literal["live", "wip", "archived"]
    problem: str
    solution_one_liner: str
    facts: list[str] = Field(default_factory=list)
    angles: list[Angle] = Field(default_factory=list)
    channels: list[str] | dict[str, ChannelWeight] = Field(default_factory=list)
    launch: dict[str, str] = Field(default_factory=dict)
    # Optional: for projects that have visual content to fetch (e.g., Kopi email designs)
    content_source: dict | None = None

    @property
    def channel_names(self) -> list[str]:
        """Return channel names regardless of whether `channels` is a list or weighted dict."""
        if isinstance(self.channels, dict):
            return list(self.channels.keys())
        return list(self.channels)

    def weight_for(self, channel: str) -> float:
        if isinstance(self.channels, dict):
            cw = self.channels.get(channel)
            return cw.weight if cw else 1.0
        return 1.0


class Registry(BaseModel):
    projects: dict[str, Project]

    def live_projects(self) -> dict[str, Project]:
        return {name: p for name, p in self.projects.items() if p.status == "live"}

    def get(self, name: str) -> Project:
        return self.projects[name]


def load(path: Path | str = "projects.yml") -> Registry:
    """Load and validate projects.yml."""
    raw = _yaml.load(Path(path).read_text())
    if raw is None:
        return Registry(projects={})
    return Registry(projects={name: Project.model_validate(dict(data)) for name, data in raw.items()})


def load_raw(path: Path | str = "projects.yml"):
    """Return the ruamel.yaml document for in-place mutation (preserves comments)."""
    return _yaml.load(Path(path).read_text())


def save_raw(doc, path: Path | str = "projects.yml") -> None:
    """Persist a mutated ruamel.yaml document back to disk."""
    with Path(path).open("w") as f:
        _yaml.dump(doc, f)
