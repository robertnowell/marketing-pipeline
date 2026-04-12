I wanted to tell my girlfriend 'I missed you today' in Farsi and have it land right — not phrasebook-stiff, not accidentally formal in a way that reads cold. Google Translate gives one answer. It doesn't tell you whether that answer sounds like a text message or a letter to a government office.

So I built konid: you give it anything you want to say, it returns three versions ordered casual to formal, with a note on register and cultural context for each. Mandarin, Japanese, Korean, Spanish, French, German, Portuguese, Italian, Russian, Arabic, Hindi, and a few more — 13+ total. Audio pronunciation plays directly through your speakers via node-edge-tts, no API key required.

The three-option structure is the whole point. For 'I missed you today' in Spanish you might get:

1. *Te extrañé hoy* — casual, direct, what you'd text
2. *Hoy te he echado de menos* — slightly warmer, more felt, common in Spain
3. *Tu ausencia se hizo notar hoy* — formal, almost literary, wrong register for a partner

The nuance note tells you which to pick and why. That's the thing a phrasebook skips.

I use it as an MCP server inside Claude Code:

```bash
claude mcp add konid-ai -- npx -y konid-ai
```

Also works in Cursor, VS Code Copilot, Windsurf, Zed, JetBrains, and Claude Cowork. If you're on ChatGPT, enable Developer mode and add the endpoint `https://konid.fly.dev/mcp`.

The name: konid (کنید) is Farsi for 'do' — take action.

MIT licensed. github.com/robertnowell/konid-language-learning