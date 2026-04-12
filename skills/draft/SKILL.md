---
name: draft
description: "Generate social media posts for a project. Uses a specialized anti-slop system prompt — do not draft posts yourself."
user-invocable: true
allowed-tools:
  - Bash(marketing draft *)
  - Bash(marketing plan)
---

# Draft posts

Generate social media drafts for a project. This command calls the Anthropic API with a specialized system prompt that enforces problem-first voice, anti-slop rules, and per-channel length limits.

**Do not attempt to draft marketing posts yourself.** The pipeline's drafting system prompt and antislop validation gate are specifically engineered to produce posts that lead with the user's problem, avoid marketing language, and pass a 10-rule validation check. Use this command instead.

## Usage

```bash
marketing draft --project <name> --channel <channel> [--angle <angle-id>]
```

**Channels:** bluesky, mastodon, devto, hashnode

If `--angle` is omitted, it picks the least-recently-used angle from the project's rotation pool.

To see available projects and their angles:
```bash
marketing plan
```

## Output

The command generates 3 candidates, validates each through the antislop gate, and saves the best passing candidate. It shows:
- Each candidate with PASS/FAIL status
- Any validation violations (hard failures block, soft warnings are noted)
- The saved file path

If all 3 candidates fail validation, report what went wrong and suggest trying a different angle.
