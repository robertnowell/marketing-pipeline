"""Directory listing automation — data-driven from surfaces.yml.

Reads the resolved directories for a project (audience + kind layering)
from surfaces.yml and generates submission commands/payloads for each.
Adding a new project type or directory means editing surfaces.yml, not Python.
"""

from __future__ import annotations

import shlex
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from ruamel.yaml import YAML

from pipeline.registry import Project
from pipeline.surfaces import Directory, SurfaceRegistry

_yaml = YAML()
_yaml.default_flow_style = False


@dataclass
class DirectorySubmission:
    directory: str
    method: Literal["cli", "api", "github_topics", "pr", "web_form", "manual"]
    command: str | None = None
    url: str | None = None
    payload: dict | None = None
    pr_body: str | None = None
    notes: str | None = None
    automated: bool = False


@dataclass
class ListingPlan:
    project_name: str
    repo_url: str
    submissions: list[DirectorySubmission] = field(default_factory=list)

    @property
    def automated(self) -> list[DirectorySubmission]:
        return [s for s in self.submissions if s.automated]

    @property
    def manual(self) -> list[DirectorySubmission]:
        return [s for s in self.submissions if not s.automated]


# --- Cascade notes for well-known directories ---
CASCADE_NOTES: dict[str, str] = {
    "mcp-registry": "Cascades to: Glama (24-48h), PulseMCP (daily), GitHub MCP Registry (hourly).",
    "smithery": "Targets Smithery registry only.",
    "glama": "Also auto-indexes from official MCP Registry within 24-48h.",
    "pulsemcp": "Run by MCP Steering Committee. Weekly newsletter — high-signal.",
}


def plan_listings(
    project: Project,
    project_name: str,
    surfaces_path: Path | str = "surfaces.yml",
) -> ListingPlan:
    """Generate a submission plan from surfaces.yml — no hardcoded routing."""
    repo = project.repo
    repo_url = repo if repo.startswith("https://") else f"https://github.com/{repo}"
    repo_slug = repo_url.removeprefix("https://github.com/")
    plan = ListingPlan(project_name=project_name, repo_url=repo_url)

    # 1. GitHub topics (always, for auto-indexing)
    topics = _github_topics_from_kind(project.kind)
    if topics:
        plan.submissions.append(DirectorySubmission(
            directory="GitHub Topics",
            method="github_topics",
            command=f"gh api repos/{repo_slug}/topics -X PUT -f " + " -f ".join(f"names[]={t}" for t in topics),
            notes=f"Sets: {', '.join(topics)}. Triggers auto-indexing by SkillsMP, claudemarketplaces.com.",
            automated=True,
        ))

    # 2. All directories from surfaces.yml (audience + kind layering)
    surfaces = SurfaceRegistry.load(surfaces_path)
    resolved = surfaces.resolve(project)

    for directory in resolved.directories:
        sub = _directory_to_submission(directory, project, project_name, repo_url, repo_slug)
        if sub is not None:
            plan.submissions.append(sub)

    return plan


def _directory_to_submission(
    d: Directory,
    project: Project,
    project_name: str,
    repo_url: str,
    repo_slug: str,
) -> DirectorySubmission | None:
    """Convert a surfaces.yml Directory to a DirectorySubmission."""
    cascade = CASCADE_NOTES.get(d.name, "")

    if d.type == "cli" and d.tool:
        # CLI-based automated submission
        if d.tool == "mcp-publisher":
            command = "mcp-publisher publish"
        elif d.tool == "smithery-cli":
            command = f"smithery mcp publish {repo_url} -n {repo_slug}"
        else:
            command = d.tool
        notes = f"Requires {d.tool} CLI."
        if cascade:
            notes += f" {cascade}"
        return DirectorySubmission(
            directory=d.name,
            method="cli",
            command=command,
            notes=notes,
            automated=True,
        )

    if d.type == "pr" and d.repo:
        # GitHub PR submission
        pr_body = (
            f"## Add {project_name}\n\n"
            f"**Repository:** {repo_url}\n"
            f"**Description:** {project.solution_one_liner}\n"
            f"**Problem:** {project.problem}\n\n"
            f"Open source, actively maintained.\n"
        )
        return DirectorySubmission(
            directory=d.name,
            method="pr",
            url=f"https://github.com/{d.repo}",
            pr_body=pr_body,
            notes=f"Fork + PR to {d.repo}. {cascade}".strip(),
        )

    if d.type == "form" and d.url:
        # Web form submission
        notes = "Web form submission."
        if cascade:
            notes += f" {cascade}"
        return DirectorySubmission(
            directory=d.name,
            method="web_form",
            url=d.url,
            notes=notes,
        )

    if d.type == "contact" and d.contact:
        return DirectorySubmission(
            directory=d.name,
            method="manual",
            notes=f"Contact: {d.contact}",
        )

    return None


def _github_topics_from_kind(kind: str) -> list[str]:
    """Generate GitHub topics from kind(s). Supports comma-separated."""
    topics: list[str] = []
    for k in kind.split(","):
        k = k.strip().lower()
        if k in ("mcp-server", "mcp_server", "mcp"):
            topics.extend(["mcp", "mcp-server", "model-context-protocol"])
        elif k in ("claude-skill", "claude_skill", "claude-plugin", "skill"):
            topics.extend(["claude-skill", "claude-code", "anthropic"])
        elif k in ("browser-extension", "chrome-extension", "extension"):
            topics.extend(["browser-extension", "chrome-extension", "firefox-addon"])
        elif k in ("terminal-theme",):
            topics.extend(["terminal-theme", "color-scheme"])
    topics.append("open-source")
    # Dedupe preserving order
    seen: set[str] = set()
    return [t for t in topics if not (t in seen or seen.add(t))]


def execute_automated(
    plan: ListingPlan, dry_run: bool = False, max_attempts: int = 2,
) -> list[tuple[str, bool, str]]:
    """Execute all automated submissions in a plan."""
    results = []
    for sub in plan.automated:
        if sub.command is None:
            continue
        if dry_run:
            results.append((sub.directory, True, f"[dry run] would run: {sub.command}"))
            continue

        last_output = ""
        success = False
        for attempt in range(1, max_attempts + 1):
            try:
                result = subprocess.run(
                    shlex.split(sub.command),
                    shell=False,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                success = result.returncode == 0
                last_output = (result.stdout if success else result.stderr).strip()
                if success:
                    break
            except Exception as e:
                last_output = str(e)
            if attempt < max_attempts:
                time.sleep(2)

        results.append((sub.directory, success, last_output))

    return results


def save_listing_status(plan: ListingPlan, results: list[tuple[str, bool, str]]) -> Path:
    """Save listing status to reports/{project}/listing-status.yml."""
    reports_dir = Path("reports") / plan.project_name
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / "listing-status.yml"

    status: dict = {
        "project": plan.project_name,
        "repo": plan.repo_url,
        "submissions": {},
    }
    result_map = {name: (success, output) for name, success, output in results}

    for sub in plan.submissions:
        entry: dict = {
            "method": sub.method,
            "automated": sub.automated,
        }
        if sub.directory in result_map:
            success, output = result_map[sub.directory]
            entry["status"] = "submitted" if success else "failed"
            entry["output"] = output
        else:
            entry["status"] = "pending"
        if sub.url:
            entry["url"] = sub.url
        if sub.notes:
            entry["notes"] = sub.notes
        status["submissions"][sub.directory] = entry

    with path.open("w") as f:
        _yaml.dump(status, f)
    return path
