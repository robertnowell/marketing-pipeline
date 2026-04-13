# marketing-pipeline

Automated distribution pipeline for open source developer tools. Install the plugin, provide your API keys, and Claude Code becomes your marketing agent — onboarding projects, posting across 4 platforms, listing in 11+ directories, and rotating content daily. An anti-slop gate hard-rejects marketing-speak before anything ships.

## Install

Add the marketplace to your Claude Code settings (one-time):

```json
// ~/.claude/settings.json
{
  "extraKnownMarketplaces": {
    "marketing-pipeline-marketplace": {
      "source": { "source": "github", "repo": "robertnowell/marketing-pipeline" }
    }
  }
}
```

Then install:

```
/plugin install marketing-pipeline@marketing-pipeline-marketplace
```

Claude Code prompts you for API keys (Bluesky, Dev.to, Hashnode, Anthropic). They're stored in your system keychain. Dependencies install automatically on first session. That's it.

## Use

Talk to Claude:

- **"Onboard my MCP server at owner/repo"** — researches real user pain, reads the README, generates problem statement + content angles
- **"Launch it"** — posts to Bluesky, Dev.to, Hashnode, Mastodon and submits to MCP Registry, Smithery, and 9 other directories
- **"How's our engagement?"** — fetches metrics from all platforms, sends a Slack digest
- **"Run the daily cycle"** — rotates to the next angle, drafts, validates, posts

The daily cron handles rotation automatically at 14:00 UTC weekdays.

## What it does

1. **Onboard**: fetches a repo README, searches HN/Reddit/forums for real user complaints about the problem space, generates a problem statement in user language + 5 content angles
2. **Draft**: calls Claude with an anti-slop system prompt, generates 3 candidates per channel, validates each through a regex gate that hard-rejects marketing tokens, emoji, hashtags, and filler
3. **Post**: publishes to Bluesky (AT Protocol), Dev.to (Forem API), Hashnode (GraphQL), Mastodon (REST)
4. **List**: submits to MCP Registry (cascades to Glama + PulseMCP), Smithery, GitHub Topics (cascades to SkillsMP), and generates payloads for 8 more directories
5. **Report**: fetches engagement metrics, saves daily snapshots, sends a Slack digest

## Anti-slop gate

Every draft passes through `pipeline/antislop.py` before publishing. Hard-rejects:

- Marketing tokens: "excited", "game-changer", "unlock", "empower", "introducing"
- AI shorthand: "AI-powered", "AI-driven", "powered by AI"
- Emoji, hashtags, exclamation points, rhetorical questions, URL shorteners
- Filler openings: "Let's dive in", "In this post"

Quoted references are allowed (the tool can describe what it blocks). Per-channel length limits enforced: Bluesky 300 chars, Mastodon 500, Dev.to/Hashnode 150-400 words.

## Credentials needed

| Credential | Where to get it | Required |
|---|---|---|
| `ANTHROPIC_API_KEY` | [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys) | Yes |
| `BLUESKY_HANDLE` + `BLUESKY_APP_PASSWORD` | bsky.app → Settings → Privacy → App Passwords | Yes |
| `DEVTO_API_KEY` | dev.to → Settings → Extensions | Yes |
| `HASHNODE_PAT` + `HASHNODE_PUBLICATION_ID` | hashnode.com → Account Settings → Developer | Yes |
| `MASTODON_ACCESS_TOKEN` + `MASTODON_INSTANCE_URL` | Your instance → Preferences → Development | No |
| `SLACK_WEBHOOK_URL` | api.slack.com/apps → Incoming Webhooks | No |

## Supported surfaces

**Automated posting:** Bluesky, Dev.to, Hashnode, Mastodon

**Automated directory listing:** MCP Registry (→ cascades to Glama, PulseMCP), Smithery, GitHub Topics (→ cascades to SkillsMP, claudemarketplaces.com)

**Submit with generated payloads:** awesome-claude-code, awesome-claude-plugins, awesome-claude-skills, skillsdirectory.com, awesomeclaude.ai, DevHunt, Uneed, Claude Plugin Marketplace

## Project types

The `kind` field routes projects to the right directories:

- `mcp-server` → MCP Registry, Smithery, Glama, PulseMCP, mcp.so, mcpservers.org
- `claude-skill` → Claude Plugin Marketplace, awesome-claude-code, SkillsMP
- `browser-extension` → Chrome Web Store, Firefox AMO, Edge Add-ons
- `terminal-theme` → iTerm2 Color Schemes, base16, Gogh

## Development

For contributing or running outside the plugin:

```bash
git clone https://github.com/robertnowell/marketing-pipeline
cd marketing-pipeline
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env    # fill in credentials
marketing setup         # verify what's configured
pytest tests/           # 72 tests
```

## License

MIT
