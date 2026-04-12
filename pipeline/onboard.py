"""Auto-onboard a new project by reading its README and generating registry fields.

Fetches the repo README via GitHub API, sends it to Claude with a structured
extraction prompt, and returns a complete projects.yml entry with problem,
solution_one_liner, facts, and angles — all grounded in what the README actually says.
"""

from __future__ import annotations

import json

import anthropic
import httpx

from pipeline.config import Config

ONBOARD_SYSTEM_PROMPT = """\
You are extracting structured marketing metadata from a GitHub repository README.
Your output will feed an automated marketing pipeline that generates social posts
about developer tools. Every field you produce must be grounded in what the README
actually says — do not invent features or capabilities.

The pipeline's voice rules:
- Lead with the USER'S problem, not the technology
- No marketing language (no "game-changer", "unlock", "empower", "AI-powered")
- Specifics over enthusiasm: numbers, constraints, concrete details
- First person, practitioner-to-practitioner tone

Output a JSON object with these fields:

{
  "problem": "1-2 sentences describing the concrete problem this tool solves, in the
               language a frustrated user would use. Start with what breaks or annoys.",
  "solution_one_liner": "One sentence: what the tool does. Not a tagline — a description.",
  "facts": ["5-8 specific, verifiable facts from the README. Numbers, supported platforms,
             technical choices, constraints. Each must be directly stated in the README."],
  "angles": [
    {"id": "launch", "summary": "The launch angle — why this exists, what motivated building it"},
    {"id": "problem-specific", "summary": "A specific problem scenario the tool solves"},
    {"id": "how-it-works", "summary": "One interesting technical or design choice"},
    {"id": "comparison", "summary": "How this differs from the obvious alternative"},
    {"id": "use-case", "summary": "A concrete use case from the README or implied by it"}
  ]
}

Return ONLY valid JSON. No markdown fences, no commentary.
"""


def fetch_readme(repo: str) -> str:
    """Fetch a repo's README via GitHub API. repo is 'owner/name' or full URL."""
    repo = repo.removeprefix("https://github.com/")
    resp = httpx.get(
        f"https://api.github.com/repos/{repo}/readme",
        headers={"Accept": "application/vnd.github.raw+json"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.text


def generate_entry(readme: str, repo: str, kind: str, audience: str, config: Config) -> dict:
    """Send README to Claude and get back a structured project entry."""
    api_key = config.require_anthropic()
    client = anthropic.Anthropic(api_key=api_key)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=ONBOARD_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": (
                f"Repository: {repo}\n"
                f"Kind: {kind}\n"
                f"Target audience: {audience}\n\n"
                f"README contents:\n\n{readme[:12000]}"
            ),
        }],
    )

    raw = response.content[0].text.strip()
    # Strip markdown fences if present
    if raw.startswith("```"):
        lines = raw.split("\n")
        lines = [line for line in lines if not line.startswith("```")]
        raw = "\n".join(lines).strip()

    parsed = json.loads(raw)

    # Build the full projects.yml entry
    return {
        "repo": repo if repo.startswith("https://") else f"https://github.com/{repo}",
        "kind": kind,
        "audience": audience,
        "status": "live",
        "problem": parsed["problem"],
        "solution_one_liner": parsed["solution_one_liner"],
        "facts": parsed["facts"],
        "angles": parsed["angles"],
    }
