I wanted to tell my girlfriend 'I missed you today' in Farsi and have it land the way it would from someone who grew up speaking it — not the way a phrasebook would render it. Every translation tool I tried gave me one answer, no explanation of whether it was too stiff, too casual, or just technically correct but emotionally flat.

So I built konid: you give it a phrase, it gives you three versions ordered casual to formal, with the register explained and cultural context for why the options differ. For tender or emotionally loaded phrases, that difference matters. 'I missed you' in Japanese, for example, splits into registers that carry completely different weight depending on who you're speaking to and what you want to signal.

The name is Farsi — كنيد means 'do.'

**What it actually does**

Every query returns:
- Three translations, casual → formal
- A register note on each (what relationship or context it fits)
- A nuance comparison explaining what changes between them
- Audio pronunciation played through your speakers via node-edge-tts — no API key, no copy-pasting into a second tab

It supports 13+ languages: Mandarin, Japanese, Korean, Spanish, French, German, Portuguese, Italian, Russian, Arabic, Hindi, and more.

**How to run it**

Installs as an MCP server — one command and it works in Claude Code, Cursor, VS Code Copilot, Windsurf, Zed, JetBrains, and Claude Cowork:

```bash
claude mcp add konid-ai -- npx -y konid-ai
```

Also available as a ChatGPT app via Developer mode using the endpoint `https://konid.fly.dev/mcp`.

The problem it solves isn't translation — translation is solved. The problem is that a single literal answer teaches you nothing and often sounds wrong to a native speaker in ways you can't detect. Three options with the register explained at least tells you what you're choosing between.

MIT licensed. github.com/robertnowell/konid-language-learning