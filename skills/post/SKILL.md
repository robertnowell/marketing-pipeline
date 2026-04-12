---
name: post
description: "Publish a draft to a social channel (Bluesky, Dev.to, Hashnode, or Mastodon)."
user-invocable: true
allowed-tools:
  - Bash(marketing post *)
---

# Post a draft

Publish a previously generated draft to a channel.

```bash
marketing post --channel <channel> --project <name> --file <path-to-draft> [--dry-run]
```

**Channels:** bluesky, devto, hashnode, mastodon

Always confirm with the user before posting without `--dry-run`. Show them the draft content first.

On success, the command prints the post URL and tracks it in the manifest for engagement reporting.
