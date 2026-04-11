# Simulated week 1 — bar-setting dry run (v2, desire-anchored voice)

**What this is:** 24 posts across 7 days, 4 projects, 4 channels — hand-authored against the revised rules in `prompts/draft_post.md` ("lead with the pain, not the technology"). First-person stories and concrete lived moments replace engineering-first framing. This is v2; v1 was rejected for leading with features and specifics instead of the reader's actual desire.

**The voice rule**: every post opens with a concrete moment, lived desire, or cultural hook that names the pain in the reader's own words. The tool appears after the motivation lands. Specifics serve the desire, never replace it.

**Project desire anchors** (from projects.yml `problem` fields):
- **konid** — talking to a loved one in their first language without sounding like a phrasebook / daily professional translation as a learning loop
- **rabbitholes** — Wikipedia on every page / all the world's knowledge one highlight away
- **klein-blue** — Claude Code is 80% prose, not code / Yves Klein's IKB as one anchor pigment you actually care about
- **skill-tree** — using Claude daily but not knowing if you're getting better / running Anthropic's 11-behavior Fluency classification against your own session history

---

## Day 1 — Monday (Bluesky rotation, angle 1)

### 1. konid × bluesky × girlfriend-language

> I tried to tell my girlfriend 'I missed you today' in her language and everything sounded like a cue card. konid returns three options — casual, neutral, tender — with the register and cultural context for each. github.com/robertnowell/konid-language-learning

*278 chars*

### 2. rabbitholes × bluesky × wikipedia-everywhere

> The thing I always wanted was Wikipedia on every page. Every article has words I half-know, concepts that would open up if I just knew what they meant. rabbitholes does it — highlight anything, read the explanation inline, click any word to go deeper. github.com/robertnowell/rabbitholes

*295 chars*

### 3. klein-blue × bluesky × prose-not-code

> Claude Code is mostly prose — tool output, reasoning, permission prompts. I read paragraphs for hours every day. Most terminal themes optimize for code syntax. klein-blue is built around one Yves Klein pigment, tuned for reading prose at body size. github.com/robertnowell/klein-blue

*285 chars*

### 4. skill-tree × bluesky × am-i-getting-better

> I've used Claude every day for months and I have no idea if I'm getting better or just getting faster at the same habits. skill-tree classifies your session history against the 11 behaviors from Anthropic's Fluency Index. github.com/robertnowell/ai-fluency-skill-cards

*275 chars*

---

## Day 2 — Tuesday (Mastodon rotation, angle 2)

### 5. konid × mastodon × translate-and-learn

> I translate Japanese emails for work every day in a language I'm still learning. For years, the tool I was using got me through the task but I wasn't picking anything up — I'd look at the translation, hit send, and immediately forget. konid returns three register options per phrase with the nuance between them explained, so every email becomes a tiny language lesson instead of just a utility. github.com/robertnowell/konid-language-learning

*485 chars*

### 6. rabbitholes × mastodon × half-known-concepts

> Every paper I read has a few concepts I half-know. 'Bayesian inference.' 'Mechanistic interpretability.' 'Pareto frontier.' I have a fuzzy sense of each one but skipping past them leaves me with a shallow read. rabbitholes lets me highlight any of them and get a real explanation inline next to the text, with every word in the response clickable as a new entry point. Wikipedia on every page, all the time. github.com/robertnowell/rabbitholes

*480 chars*

### 7. klein-blue × mastodon × ikb-mystique

> Yves Klein spent years trying to capture one specific blue. In 1960 he registered it as 'the color of the void' — International Klein Blue, #002FA7. It doesn't look like decoration. You look INTO it, not AT it. klein-blue is four Claude Code terminal themes built around that one pigment, tuned for prose reading over long sessions. github.com/robertnowell/klein-blue

*450 chars*

### 8. skill-tree × mastodon × fluency-on-my-conversations

> In February, Anthropic put out a study measuring 11 collaboration behaviors across 9,830 real Claude conversations. It was the first actual baseline for what productive use of a model looks like, at population scale. I wanted to know what MINE look like against that baseline. skill-tree runs the same classification on your own session history and assigns you one of seven archetypes. github.com/robertnowell/ai-fluency-skill-cards

*475 chars*

---

## Day 3 — Wednesday (Dev.to long-form)

### 9. konid × devto × register-matters

**Title**: Every translation tool acts like there's one right answer. There isn't.

My girlfriend's first language isn't English. When I try to say something meaningful to her in her language, Google Translate gives me one answer and hides the fact that there are several — each with a different register, a different emotional temperature, a different thing it says about us.

Here's the one that broke it for me. I wanted to say 'I missed you today.' I wanted it to sound tender, not clinical. Translate gave me the clinical version. Not a bug in translation quality — a bug in the UX assumption that one answer is enough.

konid returns three options per phrase, ordered casual → neutral → tender (or casual → formal, depending on what applies):

```
You: how do I say 'we'll see' in Chinese?

konid:
1. 再说吧 (zài shuō ba) — casual, slightly evasive, functions as a soft 'no'
2. 看情况吧 (kàn qíngkuàng ba) — 'depends on the situation', genuinely open
3. 到时候再看吧 (dào shíhou zài kàn ba) — 'wait and see', most neutral
```

Each option explains the register, the cultural context, and when a native speaker would actually use it. Audio plays through your speakers for the tones and contour.

Works as an MCP server across Claude Code, Cursor, VS Code, Windsurf, Zed, JetBrains, Claude Cowork, and as a ChatGPT app at konid.fly.dev/mcp. Installs in Claude Code with:

```
claude mcp add konid-ai -- npx -y konid-ai
```

Supports 13+ languages. MIT licensed.

The reason I built it: I wanted a language tool that assumes you're going to actually use what it gives you, in a real relationship, with a real person. One answer hides the choice. Three options makes you think about who you're talking to — which is the whole point of learning a language in the first place.

github.com/robertnowell/konid-language-learning

*~350 words*

### 10. rabbitholes × devto × wikipedia-everywhere

**Title**: I wanted Wikipedia on every page. So I built it.

There's a particular feeling when you're reading a paper and every few paragraphs has a concept you half-know — 'Bayesian inference,' 'mechanistic interpretability,' 'Pareto frontier,' 'the ergodic hypothesis.' You have a rough sense of each one, but not well enough to trust the argument that depends on it. You could open a new tab, look it up, read the Wikipedia article, come back. But by the time you come back, the thread you were actually following is gone.

I wanted Wikipedia on every page. Not for Wikipedia articles specifically — for every article. Every webpage. Every concept I hit. All the world's knowledge one highlight away, without ever leaving the page I'm reading.

rabbitholes is a Chrome extension that does it. Highlight any word or phrase on any page. A shadow-DOM tooltip renders an explanation from Claude Haiku 4.5 next to your cursor. Every word in the response is clickable — click 'ergodic' and you get a new explanation about ergodicity, with its own clickable words. Keep going as deep as you want.

Two extras:

- **The globe icon** re-answers the current query enriched with Brave Search results, with source chips you can click if you want to verify.
- **The rabbit-hole counter** tracks how many hops deep you've gone from the original highlight. Like the Wikipedia game where you click 'first link' and end up at Philosophy, but for any article on any page.

```
Trail: quantum entanglement → Bell's theorem → hidden variables →
       realism → metaphysics → philosophy
```

Six hops. Shareable as a tweet-sized breadcrumb.

Zero analytics, zero telemetry, no intermediary server. Every request goes straight from your browser to api.anthropic.com or api.search.brave.com. Keys in chrome.storage.sync, never leave your machine. Manifest V3.

github.com/robertnowell/rabbitholes

*~355 words*

---

## Day 4 — Thursday (Dev.to long-form)

### 11. klein-blue × devto × prose-not-code

**Title**: Claude Code is 80% prose. Most terminal themes are optimizing for the wrong thing.

I spent a weekend last month switching between terminal themes for Claude Code and noticed something nobody had told me: almost nothing on my screen during a Claude session is code.

Tool output is prose. Permission prompts are prose. Claude's reasoning is prose. Diagnostic errors are prose. Diffs are half prose (file paths, change descriptions, line counts) and half code. The only slot that's actually code is the content of the files being edited — and even that you're reading in fragments, not consuming like a source tree.

Popular terminal themes optimize for code syntax highlighting. Keywords pop. Strings pop. Comments fade. Everything else — the 80% that's actually prose in a Claude Code session — is an afterthought. The result is a theme tuned for the wrong distribution.

klein-blue is four terminal themes built the other way. Prose first, with syntax highlighting as the secondary concern. One anchor color — Yves Klein's IKB #002FA7 — used surgically instead of a full 16-color palette fighting for attention. APCA contrast verification with per-role gates:

```
body text          Lc ≥ 90
subtle fg tier     Lc ≥ 75
muted comments    Lc ≥ 45
accent highlights  Lc ≥ 60
```

Four variations because the one slot that actually decides the theme's identity is ansi:redBright, which Claude Code uses for its brand orange #d77757. V1 'Refined' neutralizes it. V2 'Sand & Sea' accepts Claude's brand as a second hero. V3 'Prot' tunes it for strict legibility. V4 'Gallery' desaturates every warm channel to cream so only IKB pops.

Ships as macOS Terminal.app .terminal profile files. Built with an Objective-C builder (build.m), installs via install.sh, fully rollback-able via restore.sh. Requires Claude Code `/theme` set to dark-ansi.

github.com/robertnowell/klein-blue

*~330 words*

### 12. skill-tree × devto × what-you-avoid

**Title**: Most 'growth' tools tell you what you're already good at. That's the bug.

If you've been using Claude Code every day for a few months, you almost certainly have a plateau. A set of habits that feel efficient — you delegate a task, you skim the output, you merge the change — and because those habits feel efficient, you don't notice that you're not getting any better at the things you don't do.

Most tools that analyze collaboration habits reinforce the plateau. They tell you your strengths and suggest you do more of them. That's a local optimum. If you're great at delegating and terrible at framing problems, 'do more delegation' makes you worse, not better.

skill-tree does the inverse. It classifies your Claude Code or Cowork session history against the 11 observable behaviors from Anthropic's Fluency Index (9,830 conversations studied in Feb 2026), assigns you one of seven archetypes based on your profile, and then picks a behavior you've barely touched and turns it into a growth quest for your next session.

The 11 behaviors come from Dakan & Feller's 4D AI Fluency Framework. Three axes are observable in chat logs — Description (how you frame problems), Discernment (how you evaluate outputs), Delegation (how you decide what to hand off). The fourth (Diligence) isn't visible in session data.

For example: if your profile shows you almost never ask Claude to argue against its own proposal (a Discernment behavior), the quest might be: 'Next session, after Claude proposes an approach, ask it to argue against it.' Stored via a SessionStart hook so it's there when you start Claude Code tomorrow morning.

Install:

```
claude plugin marketplace add robertnowell/ai-fluency-skill-cards && \
claude plugin install skill-tree-ai@ai-fluency-skill-cards
```

7-step orchestration takes 30–60 seconds end-to-end. Remote classifier on Fly.io, hosted visualization with your archetype tarot card and skill radar.

Live example: skill-tree-ai.fly.dev/fixture/illuminator

github.com/robertnowell/ai-fluency-skill-cards

*~355 words*

---

## Day 5 — Friday (Bluesky rotation, angle 3)

### 13. konid × bluesky × audio-fluency

> Reading 'xiè xie' on a page and hearing a native speaker say it are different sounds. The tone contour, the vowel length, the stress — none of that survives phonetic spelling. konid plays audio for every phrase it returns. 13+ languages. github.com/robertnowell/konid-language-learning

*290 chars*

### 14. rabbitholes × bluesky × curiosity-without-losing-place

> I'm mid-paragraph in a paper and hit a term that'd be interesting to follow, but opening a tab kills the thread. rabbitholes lets me highlight it and read the explanation inline — clickable words if I want to go deeper, no new tab, no lost place. github.com/robertnowell/rabbitholes

*285 chars*

### 15. klein-blue × bluesky × four-variations

> klein-blue ships four Claude Code themes instead of one because ansi:redBright — where Claude Code shows its brand orange — is where each theme's identity lives. Neutralize it, accept as a second hero, tune for legibility, or desaturate so only IKB pops. github.com/robertnowell/klein-blue

*295 chars*

### 16. skill-tree × bluesky × archetype-card

> skill-tree classifies your Claude session history and renders your profile as one of seven tarot-card archetypes — Illuminator, Navigator, Alchemist, four others — each with museum art and a skill radar. Example: skill-tree-ai.fly.dev/fixture/illuminator github.com/robertnowell/ai-fluency-skill-cards

*300 chars*

---

## Day 6 — Saturday (Hashnode long-form)

### 17. konid × hashnode × one-server-three-clients

**Title**: I wanted one language coach across every client I use. MCP made it possible.

I use Claude Code every day. I also bounce into Cursor when I'm working on typed code, Cowork when I'm on a plane, and ChatGPT when I want voice on my phone. If I had to install a language-coaching plugin four times — one per client, each with its own plugin API, its own install flow, its own quirks — I wouldn't have built konid at all.

MCP (Model Context Protocol) is what makes it possible to write one tool and run it across every client without porting. I wrote konid once as an MCP server. Then I deployed it four ways:

- **Claude Code**: `claude mcp add konid-ai -- npx -y konid-ai` — runs locally as a node process, audio plays through your speakers.
- **Other MCP clients** (Cursor, VS Code Copilot, Windsurf, Zed, JetBrains): drop the same npx command into the client's MCP config.
- **Claude Cowork**: upload the plugin zip via 'Customize → + → Upload plugin'. Runs inside Cowork's sandbox with the same tool definitions.
- **ChatGPT**: Settings → Apps → Advanced → Developer mode → add the hosted endpoint `https://konid.fly.dev/mcp`. Same code, deployed to fly.io.

Same 13+ languages. Same three-option responses. Same cultural context notes. Same audio. Four surfaces, one implementation. I didn't have to learn three plugin APIs.

The practical upshot: if you're building a tool your users might want across multiple clients — language coaching, data lookup, custom workflows — MCP is where to invest. You write one server against `@modelcontextprotocol/sdk`, test it with one client, and the rest Just Work. The surface-specific work is packaging (npm, zip, HTTP endpoint), not logic.

If you're a user: any MCP-compatible client gets you konid. If you switch editors next year, you don't lose the tool.

github.com/robertnowell/konid-language-learning

*~355 words*

### 18. rabbitholes × hashnode × shadow-dom

**Title**: Why rabbitholes uses shadow DOM, and what broke when I tried iframes first

The first version of rabbitholes was a position-fixed div appended to document.body. Worked fine on clean sites. Broke the moment I tried it on an academic paper with custom fonts, or a news site with aggressive CSS resets. Tooltip text inherited weird line-heights. Got clipped by `overflow: hidden` on ancestors. Flashed unstyled before the extension CSS loaded.

I tried iframes next, thinking isolation would fix it. It did isolate — too much. Iframes can't inherit host fonts without injecting them yourself, and font injection into an iframe triggers FOUC every time. The tooltip would load, re-render with the right font 200ms later. Unusable for something that needs to feel instant.

Shadow DOM was the fix. Attach a shadow root to a host element, render your UI inside, and the shadow boundary blocks external CSS from bleeding in while still letting you inherit fonts via `inherit`. Internal stylesheets scope to the shadow tree and don't leak out:

```js
const host = document.createElement('div');
host.id = 'rh-host';
document.body.appendChild(host);
const shadow = host.attachShadow({ mode: 'open' });
shadow.innerHTML = `<style>/* scoped */</style><div>tooltip</div>`;
```

Result: the tooltip renders next to your cursor on news sites, documentation, academic papers, weird experimental layouts — same behavior every time. No CSS conflicts. No FOUC. No font hacks.

The broader thing rabbitholes is trying to deliver is 'Wikipedia on every page' — all the world's knowledge one highlight away, inline, without leaving the article you're reading. Shadow DOM is load-bearing for that promise. Any rendering approach that breaks on 10% of sites makes the 'every page' part a lie.

Manifest V3. Zero telemetry. Every request goes directly to api.anthropic.com. Keys in chrome.storage.sync.

github.com/robertnowell/rabbitholes

*~360 words*

### 19. klein-blue × hashnode × apca-gates

**Title**: WCAG contrast ratios lie on dark ground. Use APCA with per-role gates.

WCAG 2.1 says 4.5:1 contrast is enough for body text. It isn't — especially not on dark terminal backgrounds. The WCAG ratio is a luminance math trick that doesn't model how human vision actually processes dark-ground text. You can pass WCAG with a #6a6a8c muted gray on #0a0a12 black and the result is text that's genuinely hard to read at body size, for more than a few minutes.

This matters for Claude Code more than almost any other terminal workload because Claude Code is mostly prose. Tool output. Reasoning. Permission prompts. Explanations. You're reading paragraphs, not scanning syntax. If your theme passes WCAG but your eyes hurt at hour four, WCAG was the wrong gate.

APCA (Accessible Perceptual Contrast Algorithm) is the proposed replacement being fought over for WCAG 3. It's rooted in psychophysical studies and outputs a Lc (Lightness contrast) value roughly in the range [-108, 108]. For readable body text on a dark ground, you want Lc magnitudes around 90 or higher.

klein-blue uses APCA with per-role gates, not a single floor:

```
body text          Lc ≥ 90
subtle fg tier     Lc ≥ 75
muted comments    Lc ≥ 45
accent highlights  Lc ≥ 60
```

Each role serves a different job. Body text needs to be read continuously; muted comments are glance-able at best. A single 90 floor kills the muted tier (nothing looks de-emphasized at 90), a single 60 floor makes body text painful.

V3 'Klein Void Prot' is the only variation where every accent passes strict gates. V1, V2, V4 break specific gates on purpose — V4's 'desaturated to cream' channels fail on hue shift because the philosophy is 'only IKB pops, everything else is ground'.

The verifier (apca.py) runs against each variation's build.m output. Change a hex, drop below the gate for its role, build.sh fails loud.

github.com/robertnowell/klein-blue

*~360 words*

### 20. skill-tree × hashnode × cowork-home

**Title**: How Cowork's ephemeral $HOME forced skill-tree's dual-state-path design

skill-tree's whole point is that it persists a growth quest across Claude sessions. You finish a session, the tool gives you a specific behavior to try next time — 'after Claude proposes an approach, ask it to argue against it' — and tomorrow morning when you start Claude Code, the quest surfaces before you do anything else. If the quest doesn't survive between sessions, the tool is just a one-shot report, not a growth loop.

Claude Code was easy. Write the quest to `~/.skill-tree/quest.json`. Every session on the same machine sees it. Done.

Cowork broke that. Cowork runs in a sandboxed environment where each session gets a fresh $HOME directory — whatever you wrote last session is gone by the time the next session starts. The quest evaporates. Which means the growth loop doesn't work.

The fix was a dual-state-path. Claude Code writes to `~/.skill-tree/`. Cowork writes to `$CLAUDE_PLUGIN_ROOT/.user-state/`. That second path lives inside the installed plugin's directory, which Cowork persists across sessions as part of the plugin itself. The quest survives — with one caveat: when the plugin is updated, the plugin directory gets replaced and the user-state with it. Claude Code's path survives plugin updates too, because `~/.skill-tree/` lives outside the plugin.

So Claude Code gets the more durable path, Cowork gets the best available option within the sandbox constraints, and the SessionStart hook runs the same check in both — 'is there an active quest?', load it, display it, mark it completed when the session ends.

The actual read/write is maybe 30 lines of TypeScript. The design thinking was the interesting part. You can't build cross-runtime plugins by assuming one filesystem. Each runtime has its own escape hatches for persistent state, and finding them is half the work.

github.com/robertnowell/ai-fluency-skill-cards

*~335 words*

---

## Day 7 — Sunday (Mastodon rotation, angle 4)

### 21. konid × mastodon × girlfriend-language (second story beat)

> Her name is Min. She's from Chongqing. Her English is perfect, which is why I never bothered to learn much Mandarin beyond 'ni hao' — until I realized I was missing out on the whole texture of who she is in her first language. konid gives me three register options for any phrase I want, with the cultural context for each. I'm slowly building a vocabulary I actually use. github.com/robertnowell/konid-language-learning

*440 chars*

### 22. rabbitholes × mastodon × philosophy-counter

> There's a game on Wikipedia where if you click the first non-parenthetical link in every article, ~97% of paths converge on Philosophy. rabbitholes has a version of that for any webpage. The counter tracks how many hops deep you've gone from the original highlight, and when your trail hits 'philosophy' anywhere, you get a shareable breadcrumb of every concept you touched. Six hops from a physics paper to metaphysics. github.com/robertnowell/rabbitholes

*475 chars*

### 23. klein-blue × mastodon × reading-for-hours

> Reading code for a few minutes and reading prose for eight hours are different workloads. The first needs syntax highlighting. The second needs comfortable body-size legibility, enough visual rest that your eyes don't burn at hour four, and a single anchor color you actually like looking at. klein-blue is four Claude Code terminal themes built around Yves Klein's IKB for the second workload. github.com/robertnowell/klein-blue

*460 chars*

### 24. skill-tree × mastodon × what-you-avoid

> Most tools that analyze your habits tell you what you're good at and suggest you do more of it. That's a local optimum. If you're great at delegating and terrible at framing problems, 'do more delegation' makes you worse. skill-tree does the inverse — it picks a behavior you've barely touched and turns it into a specific growth quest for your next Claude session. github.com/robertnowell/ai-fluency-skill-cards

*440 chars*

---

## Week summary

| Day | Channel | Posts | Form | Projects covered |
|---|---|---|---|---|
| Mon | bluesky | 4 | short | all 4 |
| Tue | mastodon | 4 | short | all 4 |
| Wed | dev.to | 2 | long | konid, rabbitholes |
| Thu | dev.to | 2 | long | klein-blue, skill-tree |
| Fri | bluesky | 4 | short | all 4 |
| Sat | hashnode | 4 | long | all 4 |
| Sun | mastodon | 4 | short | all 4 |
| **Total** | | **24** | 8 long / 16 short | Each project: 6 posts/week |

## What changed from v1 to v2

Every short-form post now opens with a **lived moment or stated desire** instead of a feature statement:

| v1 opener | v2 opener |
|---|---|
| "Google Translate tells Spanish learners 'estoy caliente' means 'I'm hot'." | "I tried to tell my girlfriend 'I missed you today' in her language and everything sounded like a cue card." |
| "Tab-switching kills web research." | "The thing I always wanted was Wikipedia on every page." |
| "Pure IKB #002FA7 fails APCA as terminal text — Lc -12." | "Claude Code is mostly prose — tool output, reasoning, permission prompts. I read paragraphs for hours every day." |
| "Anthropic's Fluency Index studied 9,830 Claude conversations." | "I've used Claude every day for months and I have no idea if I'm getting better or just getting faster at the same habits." |

The specifics (Lc -12, 9,830 conversations, IKB #002FA7) still appear, but **in service of** the desire, never as the lead. The reader arrives at the specifics with motivation already loaded.

## What the drafter has to do to match this bar

1. **Read the `problem` field from `projects.yml` and lead with a specific instantiation of it.** The problem field is now written as a first-person story or stated desire; the drafter should pick a concrete moment inside that story as the opening.
2. **Never put a specification in the first sentence.** Numbers, constraints, hex codes, API details — all appear in the middle or end, never the lead.
3. **One post = one angle = one story beat.** The konid girlfriend-language angle has multiple valid story beats ("I tried to say 'I missed you'", "Her name is Min, her English is perfect"). The drafter should vary the beat without reframing the angle.
4. **Long-form still anchors on a lived moment.** Post #9 opens with a relationship, not with translation theory. Post #10 opens with "there's a particular feeling when you're reading a paper," not with shadow DOM.
5. **Technology shows up as context or justification, never as a pitch.** "MCP is what makes it possible" appears in post #17, but after four paragraphs setting up the user's cross-client workflow need.
