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

Copy `.env.example` to `.env` and fill in:

```
ANTHROPIC_API_KEY=          # for drafting (Claude Messages API)
BLUESKY_HANDLE=             # e.g. yourhandle.bsky.social
BLUESKY_APP_PASSWORD=       # from Settings → Privacy → App Passwords
DEVTO_API_KEY=              # from Settings → Extensions → API Keys
HASHNODE_PAT=               # from Developer Settings
HASHNODE_PUBLICATION_ID=    # from Dashboard → General
MASTODON_ACCESS_TOKEN=      # from Preferences → Development → New Application
MASTODON_INSTANCE_URL=      # e.g. https://hachyderm.io
```

### 3. Onboard a project

```bash
marketing onboard --name konid --repo robertnowell/konid-language-learning --kind mcp-server
```

### 4. Test

```bash
marketing draft --project konid --channel bluesky
marketing launch --project konid --dry-run
marketing cycle --dry-run
```

### 5. Go live

```bash
marketing launch --project konid
```

### GitHub Actions

Add the same env vars as repository secrets, plus:

- `NPM_TOKEN` — for automated npm publishing in the launch workflow
- The launch workflow uses `github-oidc` for MCP Registry auth (no secrets needed)

## CLI reference

| Command | What it does |
|---|---|
| `marketing plan` | Print registry summary |
| `marketing surfaces --project X` | Show resolved channels + directories |
| `marketing onboard --name X --repo owner/repo --kind mcp-server` | Auto-generate project entry from README |
| `marketing draft --project X --channel bluesky` | Generate 3 draft candidates, validate, save best |
| `marketing post --channel bluesky --file path.md` | Publish a draft |
| `marketing launch --project X [--dry-run]` | Submit to all directories |
| `marketing cycle [--dry-run]` | Daily rotation: draft + post for all live projects |

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
