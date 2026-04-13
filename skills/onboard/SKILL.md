---
name: onboard
description: "Add a new open source project to the marketing pipeline. Researches real user pain, auto-detects project type, generates everything."
user-invocable: true
allowed-tools:
  - Bash(marketing onboard *)
  - Bash(marketing plan)
  - WebSearch
  - WebFetch
  - Write
  - Read
---

# Onboard a new project

This is a multi-step process. Do NOT skip the research phase.

## Step 1: Gather inputs

You only need ONE thing from the user: the **GitHub repo** (owner/repo or full URL).

Everything else is auto-detected:
- **Project name** — infer from the repo name
- **Kind** — auto-detected from README (mcp-server, claude-skill, browser-extension, etc.)
- **Audience** — auto-detected from README

If the user says "onboard my project at owner/repo" that's enough to proceed.

## Step 2: Research real user pain

Before generating any marketing content, research how real people describe the problem this tool solves.

1. Read the repo's README to understand the problem space
2. Use WebSearch with 3-5 queries to find real complaints on HN, Reddit, dev forums
3. Use WebFetch to read the 2-3 most promising threads
4. Extract 10-15 exact quotes from real users describing their frustration
5. Note the vocabulary they use

Save findings to `/tmp/pain-research-{name}.md`.

## Step 3: Run the onboard command

```bash
marketing onboard --name <name> --repo <owner/repo> --pain-context /tmp/pain-research-<name>.md
```

The `--kind` flag is optional — the pipeline auto-detects it from the README. Only pass it if you want to override the detection.

## Step 4: Review

Show the user what was generated. Suggest next steps:
- "Want me to draft a Bluesky post for this?"
- "Want me to launch it to all directories?"
