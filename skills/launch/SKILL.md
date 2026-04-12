---
name: launch
description: "Launch a project to all directories, generate drafts for all channels, and post everywhere. The full launch sequence."
user-invocable: true
allowed-tools:
  - Bash(marketing launch *)
  - Bash(marketing draft *)
  - Bash(marketing post *)
  - Bash(marketing plan)
---

# Launch a project

Full launch sequence for a project: directory submissions, draft generation, and posting across all channels.

**Always recommend `--dry-run` first** so the user can review before going live.

## Steps

1. Show what will happen:
```bash
marketing launch --project <name> --dry-run
```

2. If the user approves, run the real launch:
```bash
marketing launch --project <name>
```

This will:
- Set GitHub topics for auto-indexing (automated)
- Submit to MCP Registry, Smithery (automated, if applicable to the project kind)
- Generate submission payloads for manual directories (Glama, PulseMCP, mcpservers.org, awesome-claude-code)
- Print URLs for the manual submissions

3. Generate drafts for all channels:
```bash
marketing draft --project <name> --channel bluesky
marketing draft --project <name> --channel mastodon
marketing draft --project <name> --channel devto
marketing draft --project <name> --channel hashnode
```

4. Post approved drafts:
```bash
marketing post --channel bluesky --project <name> --file <draft-path>
```

Show the user each draft before posting. If a draft fails antislop validation, explain what failed and offer to generate a new one with a different angle.
