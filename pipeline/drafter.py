"""Draft generation via Claude Messages API.

Takes a project + angle + channel from the registry, calls Claude with the
draft_post.md system prompt, and returns validated candidates. Retries once
with violation feedback if all candidates fail validation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import anthropic

from pipeline.antislop import ValidationResult, validate
from pipeline.config import Config
from pipeline.registry import Project

PROMPTS_DIR = Path(__file__).parent / "prompts"

# Exact character limits per channel — injected into the user message
# so the model knows the hard constraint, not just "short" or "concise".
CHAR_LIMITS: dict[str, int] = {
    "bluesky": 300,
    "mastodon": 500,
    "threads": 500,
    "x": 280,
}


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
    retried: bool = False

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
    the antislop validation gate. If all 3 fail, retries once with violation
    feedback so the model can correct its mistakes.
    """
    system_prompt = _load_system_prompt()
    user_message = _build_user_message(project, project_name, angle_id, channel)

    api_key = config.require_anthropic()
    client = anthropic.Anthropic(api_key=api_key)

    # First attempt
    messages = [{"role": "user", "content": user_message}]
    result = _generate_and_validate(client, model, system_prompt, messages, channel)

    if result.best is not None:
        result.project_name = project_name
        result.angle_id = angle_id
        result.channel = channel
        return result

    # All 3 failed — retry with violation feedback
    violation_summary = _summarize_violations(result.candidates)
    retry_message = (
        f"All 3 drafts failed validation. Here's what went wrong:\n\n"
        f"{violation_summary}\n\n"
        f"Generate 3 new candidates that fix ALL of these issues. "
        f"Do not repeat the same mistakes."
    )

    # Build a conversation with the failed attempt as context
    messages = [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": _candidates_to_json(result.candidates)},
        {"role": "user", "content": retry_message},
    ]

    retry_result = _generate_and_validate(client, model, system_prompt, messages, channel)
    retry_result.project_name = project_name
    retry_result.angle_id = angle_id
    retry_result.channel = channel
    retry_result.retried = True

    # Merge: if retry produced passing candidates, use those; otherwise return all failures
    if retry_result.best is not None:
        return retry_result

    # Both attempts failed — return all 6 candidates so the user can see what went wrong
    all_candidates = result.candidates + [
        DraftCandidate(text=c.text, validation=c.validation, rank=c.rank + 3)
        for c in retry_result.candidates
    ]
    return DraftResult(
        candidates=all_candidates,
        project_name=project_name,
        angle_id=angle_id,
        channel=channel,
        retried=True,
    )


def _generate_and_validate(
    client: anthropic.Anthropic,
    model: str,
    system_prompt: str,
    messages: list[dict],
    channel: str,
) -> DraftResult:
    """Call the API and validate the response."""
    response = client.messages.create(
        model=model,
        max_tokens=2048,
        system=system_prompt,
        messages=messages,
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

    return DraftResult(candidates=candidates, project_name="", angle_id="", channel=channel)


def _summarize_violations(candidates: list[DraftCandidate]) -> str:
    """Summarize all violations across candidates for the retry prompt."""
    lines = []
    for c in candidates:
        if c.validation.violations:
            issues = "; ".join(v.detail for v in c.validation.violations)
            lines.append(f"- Draft #{c.rank}: {issues}")
    return "\n".join(lines)


def _candidates_to_json(candidates: list[DraftCandidate]) -> str:
    """Format candidates as JSON for the conversation context."""
    return json.dumps([c.text for c in candidates])


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

    # Add explicit character limit for short-form channels
    if channel in CHAR_LIMITS:
        limit = CHAR_LIMITS[channel]
        payload["hard_char_limit"] = limit
        payload["length_instruction"] = (
            f"HARD LIMIT: {limit} characters maximum including the URL. "
            f"Count carefully. A post at {limit + 1} characters will be rejected. "
            f"Aim for {limit - 30}-{limit} characters to leave margin."
        )

    # Long-form channels need a title
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
