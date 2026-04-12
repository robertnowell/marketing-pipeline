"""Directory listing automation for MCP servers and Claude Code skills.

For each project, generates submission commands/payloads for all relevant
directories. Some are fully automated (CLI commands), some produce
ready-to-submit assets (PR bodies, form data) for manual submission.

Directory submission landscape (from primary-source research, April 2026):

  AUTOMATED (CLI/API):
    - Official MCP Registry: mcp-publisher publish (GitHub OIDC in CI)
    - Smithery: smithery mcp publish <url>
    - GitHub topics: add claude-skill, claude-code, mcp-server for auto-indexing

  SEMI-AUTOMATED (generate payload, human submits):
    - Glama: "Add Server" button with GitHub URL
    - PulseMCP: web form + Discord
    - mcp.so: GitHub issue submission
    - mcpservers.org: web form (~12h review)
    - awesome-claude-code: fork + PR
    - Claude plugin marketplace: form at claude.ai/settings/plugins/submit

  PULL-BASED (publish to official registry, aggregators pull):
    - Glama, PulseMCP, GitHub MCP Registry poll the official registry API hourly
    - Propagation is not guaranteed for all aggregators
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from ruamel.yaml import YAML

from pipeline.registry import Project

_yaml = YAML()
_yaml.default_flow_style = False


@dataclass
class DirectorySubmission:
    directory: str
    method: Literal["cli", "api", "github_topics", "pr", "web_form", "manual"]
    command: str | None = None        # Shell command to run
    url: str | None = None            # URL to open or submit to
    payload: dict | None = None       # Form data or API payload
    pr_body: str | None = None        # Markdown body for a PR
    notes: str | None = None          # Human-readable instructions
    automated: bool = False           # True if no human intervention needed


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


def plan_listings(project: Project, project_name: str) -> ListingPlan:
    """Generate a submission plan for a project across all relevant directories."""
    repo = project.repo
    repo_url = repo if repo.startswith("https://") else f"https://github.com/{repo}"
    # Extract owner/repo slug for CLI commands that need it
    repo_slug = repo_url.removeprefix("https://github.com/")
    plan = ListingPlan(project_name=project_name, repo_url=repo_url)

    kind = project.kind.lower()

    # Always: GitHub topics for auto-indexing
    topics = _github_topics(project)
    plan.submissions.append(DirectorySubmission(
        directory="GitHub Topics (SkillsMP auto-index)",
        method="github_topics",
        command=f"gh api repos/{repo_slug}/topics -X PUT -f " + " -f ".join(f"names[]={t}" for t in topics),
        notes=f"Sets topics: {', '.join(topics)}. SkillsMP and similar indexers pick these up automatically.",
        automated=True,
    ))

    # MCP servers: official registry + Smithery
    if kind in ("mcp-server", "mcp_server", "mcp"):
        plan.submissions.append(DirectorySubmission(
            directory="Official MCP Registry",
            method="cli",
            command="mcp-publisher publish",
            notes=(
                "Requires server.json in repo root. Auth via GitHub OIDC in CI "
                "or `mcp-publisher login github-oidc` locally. "
                "Downstream aggregators (Glama, PulseMCP) poll this registry hourly."
            ),
            automated=True,
        ))
        plan.submissions.append(DirectorySubmission(
            directory="Smithery",
            method="cli",
            command=f"smithery mcp publish {repo_url} -n {repo_slug}",
            notes="Requires smithery CLI installed. Targets Smithery registry only.",
            automated=True,
        ))
        plan.submissions.append(_mcp_so_submission(project, project_name, repo_url))
        plan.submissions.append(_mcpservers_submission(project, project_name, repo_url))
        plan.submissions.append(_pulsemcp_submission(project, project_name, repo_url))

    # Claude Code skills/plugins
    if kind in ("claude-skill", "claude_skill", "claude-plugin", "skill"):
        plan.submissions.append(DirectorySubmission(
            directory="Claude Plugin Marketplace",
            method="web_form",
            url="https://claude.ai/settings/plugins/submit",
            notes="Manual form submission. Requires Anthropic review.",
        ))

    # Glama (for both MCP servers and agent tools)
    if kind in ("mcp-server", "mcp_server", "mcp", "agent-tool"):
        plan.submissions.append(DirectorySubmission(
            directory="Glama",
            method="web_form",
            url=f"https://glama.ai/mcp/servers?add={repo_url}",
            notes="Click 'Add Server', paste GitHub URL. Claims auto-index within 24-48h.",
        ))

    # awesome-claude-code PR (for any Claude Code related tool)
    if kind in ("claude-skill", "claude_skill", "claude-plugin", "skill", "mcp-server", "mcp_server", "mcp"):
        plan.submissions.append(_awesome_claude_code_pr(project, project_name, repo_url))

    return plan


def _github_topics(project: Project) -> list[str]:
    """Determine which GitHub topics to set based on project kind."""
    kind = project.kind.lower()
    topics = []
    if kind in ("mcp-server", "mcp_server", "mcp"):
        topics.extend(["mcp", "mcp-server", "model-context-protocol"])
    if kind in ("claude-skill", "claude_skill", "claude-plugin", "skill"):
        topics.extend(["claude-skill", "claude-code", "anthropic"])
    if kind in ("browser-extension", "extension"):
        topics.extend(["browser-extension", "chrome-extension", "firefox-addon"])
    # Always include these for discoverability
    topics.append("open-source")
    return topics


def _mcp_so_submission(project: Project, name: str, repo_url: str) -> DirectorySubmission:
    """mcp.so accepts submissions via GitHub issue."""
    issue_body = (
        f"**Server Name:** {name}\n"
        f"**Repository:** {repo_url}\n"
        f"**Description:** {project.solution_one_liner}\n"
        f"**Problem it solves:** {project.problem}\n"
    )
    return DirectorySubmission(
        directory="mcp.so",
        method="web_form",
        url="https://mcp.so",
        payload={"title": f"Add {name}", "body": issue_body},
        notes="Submit via GitHub issue on mcp.so's repo or web form.",
    )


def _mcpservers_submission(project: Project, name: str, repo_url: str) -> DirectorySubmission:
    return DirectorySubmission(
        directory="mcpservers.org",
        method="web_form",
        url="https://mcpservers.org/submit",
        payload={
            "name": name,
            "description": project.solution_one_liner,
            "link": repo_url,
            "email": "",  # user fills in
        },
        notes="Web form, ~12h human review. No API.",
    )


def _pulsemcp_submission(project: Project, name: str, repo_url: str) -> DirectorySubmission:
    return DirectorySubmission(
        directory="PulseMCP",
        method="web_form",
        url="https://www.pulsemcp.com/submit",
        payload={
            "name": name,
            "url": repo_url,
            "description": project.solution_one_liner,
        },
        notes=(
            "Web form + Discord. Run by MCP Steering Committee members. "
            "Also publishes a weekly newsletter — getting listed here is high-signal."
        ),
    )


def _awesome_claude_code_pr(
    project: Project, name: str, repo_url: str,
) -> DirectorySubmission:
    pr_body = (
        f"## Add {name}\n\n"
        f"{project.solution_one_liner}\n\n"
        f"**Repository:** {repo_url}\n"
        f"**Problem:** {project.problem}\n\n"
        f"### Why this belongs here\n\n"
        f"- Solves a concrete problem for Claude Code users\n"
        f"- Open source, actively maintained\n"
    )
    return DirectorySubmission(
        directory="awesome-claude-code",
        method="pr",
        url="https://github.com/hesreallyhim/awesome-claude-code",
        pr_body=pr_body,
        notes="Fork + PR. 38k+ stars, highest-traffic Claude Code list. Human review.",
    )


def execute_automated(
    plan: ListingPlan, dry_run: bool = False, max_attempts: int = 3,
) -> list[tuple[str, bool, str]]:
    """Execute all automated submissions in a plan.

    Each command is retried up to *max_attempts* times on failure before
    recording a final result.

    Returns list of (directory_name, success, output_or_error).
    """
    import shlex
    import subprocess
    import time

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
                # Use shlex.split to avoid shell=True injection risks.
                # Commands are constructed internally but contain user-supplied
                # repo names from projects.yml.
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
                success = False
            if attempt < max_attempts:
                time.sleep(2 ** attempt)  # 2s, 4s backoff

        results.append((sub.directory, success, last_output))

    return results


def save_listing_status(plan: ListingPlan, results: list[tuple[str, bool, str]]) -> Path:
    """Save listing status to reports/{project}/listing-status.yml."""
    reports_dir = Path("reports") / plan.project_name
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / "listing-status.yml"

    status = {
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
