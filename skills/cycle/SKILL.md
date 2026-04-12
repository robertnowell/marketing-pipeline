---
name: cycle
description: "Run the daily post rotation — drafts and posts for all live projects across their channels."
user-invocable: true
allowed-tools:
  - Bash(marketing cycle *)
---

# Daily cycle

Runs the full daily rotation: for each live project, picks the least-recently-used angle, drafts a post, validates through antislop, and publishes to the first available channel.

```bash
marketing cycle --dry-run    # preview what would be posted
marketing cycle              # draft and post for real
```

**Recommend `--dry-run` first** unless the user explicitly says to post.

This is the same command that runs on the GitHub Actions daily cron (weekdays 14:00 UTC).
