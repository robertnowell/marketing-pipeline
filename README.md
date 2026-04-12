# marketing-pipeline

Automated distribution pipeline for open source developer tools. Onboard a project, and the pipeline handles directory listings, social posting, and ongoing content rotation — no daily human involvement.

Built for MCP servers, Claude Code skills, browser extensions, and agent-focused tools. Works for any OSS project with an audience definition.

## What it does

**One command to onboard:**

```bash
marketing onboard --name my-tool --repo owner/repo --kind mcp-server
```

Fetches the README, sends it to Claude, and generates: problem statement (in user language), solution one-liner, 5-8 verifiable facts, and 5 content angles. Saved to `projects.yml`.

**One command to launch:**

```bash
marketing launch --project my-tool
```

- Publishes to the official MCP Registry via `mcp-publisher` (aggregators like Glama and PulseMCP pull from it automatically)
- Publishes to Smithery
- Sets GitHub topics for auto-indexing
- Generates listing payloads for manual-submission directories
- Drafts posts for all channels (Bluesky, Mastodon, Dev.to, Hashnode)
- Posts them

**Daily cron keeps it going:**

```bash
marketing cycle
```

Rotates through projects × angles × channels. Picks the least-recently-used angle, drafts via Claude, validates through the anti-slop gate, posts.

## Anti-slop gate

Every draft passes through `pipeline/antislop.py` before it reaches a publisher. Hard-rejects:

- Marketing tokens: "excited", "game-changer", "unlock", "empower", "introducing"
- AI shorthand: "AI-powered", "AI-driven", "powered by AI"
- Emoji, hashtags, exclamation points
- Filler openings: "Let's dive in", "Buckle up", "In this post"
- Rhetorical questions: "Ever struggled with...?"
- URL shorteners

Soft-warns on technology keywords in the first sentence (the rule: lead with the problem, not the tech).

Per-channel length limits enforced: Bluesky 300 chars, Mastodon 500, X 280, Dev.to/Hashnode 150-400 words.

## Architecture

```
projects.yml          — per-project: repo, kind, audience, problem, facts, angles
surfaces.yml          — audience→channels mapping, directories, watering holes
prompts/draft_post.md — system prompt with voice rules, examples, forbidden terms

pipeline/
  config.py           — credential loading from env vars / .env
  registry.py         — Pydantic-typed loader for projects.yml
  surfaces.py         — audience+kind → channel/directory resolver
  onboard.py          — auto-generate project entry from README via Claude
  drafter.py          — draft generation via Messages API + antislop validation
  antislop.py         — regex blacklist + validation gate
  lister.py           — directory submission automation
  publish/
    bluesky.py        — AT Protocol (atproto SDK)
    devto.py          — Forem v1 API
    hashnode.py       — GraphQL (createDraft → publishDraft)
    mastodon.py       — Mastodon REST API
  cli.py              — all subcommands

.github/workflows/
  daily.yml           — cron: draft + post rotation (weekdays 14:00 UTC)
  launch.yml          — manual dispatch: full launch sequence per project
  test.yml            — lint + test on push/PR
```

## Setup

### 1. Install

```bash
git clone https://github.com/robertnowell/marketing-pipeline
cd marketing-pipeline
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. Configure credentials

```bash
cp .env.example .env
marketing setup
```

`marketing setup` checks what's configured, what's missing, and tells you exactly where to go for each one. It also verifies connectivity.

**Required** (pipeline won't draft/post without these):

| Credential | Where to get it |
|---|---|
| `ANTHROPIC_API_KEY` | [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys) |
| `BLUESKY_HANDLE` + `BLUESKY_APP_PASSWORD` | bsky.app → Settings → Privacy and security → App Passwords |
| `DEVTO_API_KEY` | dev.to → Settings → Extensions → DEV Community API Keys |
| `HASHNODE_PAT` + `HASHNODE_PUBLICATION_ID` | hashnode.com → Avatar → Account Settings → Developer |

**Optional:**

| Credential | Where to get it |
|---|---|
| `MASTODON_ACCESS_TOKEN` + `MASTODON_INSTANCE_URL` | Your instance → Preferences → Development → New Application |
| `SLACK_WEBHOOK_URL` | [api.slack.com/apps](https://api.slack.com/apps) → Create App → Incoming Webhooks |

**One-time CLI auth (for publishing):**

```bash
npm login                        # for npm package publishing
mcp-publisher login github       # for official MCP Registry (device code flow)
```

### 3. Onboard and launch a project

```bash
marketing onboard --name my-tool --repo owner/repo --kind mcp-server
marketing launch --project my-tool --dry-run   # review first
marketing launch --project my-tool             # go live
```

That's it. `onboard` reads the README and generates everything. `launch` handles directories, drafts, and posting.

### 4. Monitor

```bash
marketing status    # what's live, what's posted
marketing report    # fetch engagement metrics, send Slack digest
```

### 5. Daily automation (GitHub Actions)

Add the same env vars as repository secrets, plus:

- `NPM_TOKEN` — for automated npm publishing in the launch workflow
- `SLACK_WEBHOOK_URL` — for daily engagement digests
- The launch workflow uses `github-oidc` for MCP Registry auth (no secrets needed)

The daily cron runs `marketing cycle` + `marketing report` at 14:00 UTC weekdays.

### What's manual (can't be automated)

- **awesome-claude-code submission**: Their rules require human submission via [the issue form](https://github.com/hesreallyhim/awesome-claude-code/issues/new?template=recommend-resource.yml). One form per project, once.
- **Reviewing auto-generated angles**: `onboard` generates problem/angles from the README. They're usually good but worth a 30-second sanity check in `projects.yml`.
- **Credential rotation**: Rotate API keys periodically. Run `marketing setup` to verify everything still works.

## CLI reference

| Command | What it does |
|---|---|
| `marketing setup` | Check credentials, verify connectivity, guide through missing setup |
| `marketing status` | Show live projects, post counts, latest activity |
| `marketing onboard --name X --repo owner/repo --kind mcp-server` | Auto-generate project entry from README via Claude |
| `marketing draft --project X --channel bluesky` | Generate 3 draft candidates, validate, save best |
| `marketing post --channel bluesky --file path.md` | Publish a draft to a channel |
| `marketing launch --project X [--dry-run]` | Full launch: directories + drafts + posts |
| `marketing cycle [--dry-run]` | Daily rotation: draft + post for all live projects |
| `marketing report` | Fetch engagement metrics, save snapshot, send Slack digest |
| `marketing plan` | Print registry summary |
| `marketing surfaces --project X` | Show resolved channels + directories |

## Supported surfaces

**Automated posting:** Bluesky, Dev.to, Hashnode, Mastodon

**Automated directory listing:** Official MCP Registry, Smithery, GitHub Topics

**Manual-submit (pipeline generates payloads):** Glama, PulseMCP, mcp.so, mcpservers.org, awesome-claude-code

**Manual-post (pipeline generates drafts):** Reddit, Hacker News, LinkedIn, Product Hunt

## Project types

The `kind` field determines which directories a project is listed in:

- `mcp-server` → MCP Registry, Smithery, Glama, PulseMCP, mcp.so, mcpservers.org
- `claude-skill` → Claude Plugin Marketplace, awesome-claude-code, SkillsMP
- `browser-extension` → Chrome Web Store, Firefox AMO, Edge Add-ons
- `terminal-theme` → iTerm2 Color Schemes, base16, Gogh

The `audience` field determines social channels and tone.

## License

MIT
