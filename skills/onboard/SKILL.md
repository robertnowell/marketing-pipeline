---
name: onboard
description: "Add a new open source project to the marketing pipeline. Fetches the README, generates problem statement, facts, and content angles automatically."
user-invocable: true
allowed-tools:
  - Bash(marketing onboard *)
  - Bash(marketing plan)
---

# Onboard a new project

The user wants to add a project to the marketing pipeline. You need three pieces of information:

1. **Repository** — GitHub `owner/repo` (e.g., `robertnowell/konid-language-learning`)
2. **Kind** — what type of tool: `mcp-server`, `claude-skill`, `browser-extension`, `terminal-theme`, `cli-audit-tool`, `consumer-web-app`, `b2b-saas`
3. **Audience** (optional, defaults to `claude-code-users`) — who uses it: `mcp-users`, `claude-code-users`, `knowledge-workers`, `general-consumers`, `founders-solopreneurs`, `ecom-solopreneurs`

If the user hasn't provided all of these, ask for what's missing. Then run:

```bash
marketing onboard --name <short-name> --repo <owner/repo> --kind <kind> [--audience <audience>]
```

This fetches the repo README, sends it to Claude, and generates:
- A problem statement in user language (what breaks, what's frustrating)
- A solution one-liner
- 5-8 verifiable facts
- 5 content angles for post rotation

After onboarding, show the user what was generated and suggest next steps:
- `marketing draft --project <name> --channel bluesky` to see a sample post
- `marketing launch --project <name> --dry-run` to preview the directory listing plan
