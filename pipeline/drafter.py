"""Draft generation via Claude Messages API.

Takes a project + angle + channel from the registry, calls Claude with the
draft_post.md system prompt, and returns validated candidates.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import anthropic

from pipeline.antislop import ValidationResult, validate
from pipeline.config import Config
from pipeline.registry import Project

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


@dataclass
class DraftCandidate:
    text: str
    validation: ValidationResult
    rank: int  # 1-indexed, from the model's confidence ordering


@dataclass
class DraftResult:
    candidates: list[DraftCandidate]
    project_name: str
    angle_id: str
    channel: str

    @property
    def best(self) -> DraftCandidate | None:
        """Return the highest-ranked candidate that passed validation."""
        for c in sorted(self.candidates, key=lambda c: c.rank):
            if c.validation.passed:
                return c
        return None

    @property
    def all_passed(self) -> list[DraftCandidate]:
        return [c for c in self.candidates if c.validation.passed]


def draft(
    project: Project,
    project_name: str,
    angle_id: str,
    channel: str,
    config: Config,
    model: str = "claude-sonnet-4-6",
) -> DraftResult:
    """Generate draft posts for a project+angle+channel combination.

    Returns 3 candidates ranked by the model's confidence, each run through
    the antislop validation gate.
    """
    system_prompt = _load_system_prompt()
    user_message = _build_user_message(project, project_name, angle_id, channel)

    api_key = config.require_anthropic()
    client = anthropic.Anthropic(api_key=api_key)

    response = client.messages.create(
        model=model,
        max_tokens=2048,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    raw_text = response.content[0].text
    drafts = _parse_drafts(raw_text)

    candidates = []
    for i, draft_text in enumerate(drafts):
        validation = validate(draft_text, channel=channel)
        candidates.append(DraftCandidate(
            text=draft_text,
            validation=validation,
            rank=i + 1,
        ))

    return DraftResult(
        candidates=candidates,
        project_name=project_name,
        angle_id=angle_id,
        channel=channel,
    )


def _load_system_prompt() -> str:
    path = PROMPTS_DIR / "draft_post.md"
    return path.read_text()


def _build_user_message(
    project: Project, project_name: str, angle_id: str, channel: str,
) -> str:
    angle = next((a for a in project.angles if a.id == angle_id), None)
    if angle is None:
        raise ValueError(f"Angle '{angle_id}' not found in project '{project_name}'")

    payload = {
        "project_name": project_name,
        "problem": project.problem,
        "solution_one_liner": project.solution_one_liner,
        "facts": project.facts,
        "angle": angle.summary,
        "channel": channel,
    }

    # Long-form channels need a title — ask the model to prepend one.
    if channel in LONG_FORM_CHANNELS:
        payload["instruction"] = (
            "Prepend a title on its own line, prefixed with '# '. "
            "The title should be concise (<70 chars), problem-first, no clickbait. "
            "The JSON array should contain the full post including the title line."
        )

    return json.dumps(payload, indent=2)


LONG_FORM_CHANNELS = {"devto", "hashnode", "indiehackers"}


def _parse_drafts(raw: str) -> list[str]:
    """Parse the model's response — expected to be a JSON array of 3 strings."""
    raw = raw.strip()
    # The model sometimes wraps in markdown code fences.
    if raw.startswith("```"):
        lines = raw.split("\n")
        lines = [line for line in lines if not line.startswith("```")]
        raw = "\n".join(lines).strip()

    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [str(d) for d in parsed[:3]]
    except json.JSONDecodeError:
        pass

    # Fallback: split on double newlines if JSON parsing fails.
    parts = [p.strip() for p in raw.split("\n\n") if p.strip()]
    return parts[:3] if parts else [raw]
