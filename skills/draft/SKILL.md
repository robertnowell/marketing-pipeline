---
name: draft
description: "Generate social media posts for a project. Draft them yourself following the voice rules below, then validate with the anti-slop gate."
user-invocable: true
allowed-tools:
  - Bash(marketing validate *)
  - Bash(marketing plan)
  - Bash(cat *)
  - Read
---

# Draft posts

Generate social media drafts for a project in the marketing pipeline. YOU draft the posts directly — do not call `marketing draft` (that uses a separate API call).

## Step 1: Load project data

```bash
marketing plan
```

Then read the project's entry in projects.yml to get the problem, solution_one_liner, facts, and angles.

## Step 2: Draft following these rules

**Voice rules (non-negotiable):**
- Lead with the USER'S problem, not the technology. First sentence names the pain.
- First person, past tense where possible ("shipped", "built", "wrote")
- Specifics over enthusiasm. Fact density is a virtue; padding is the failure mode.
- No marketing tokens: "excited", "game-changer", "unlock", "empower", "introducing", "solution", "leverage", "journey"
- No AI shorthand: "AI-powered", "AI-driven", "powered by AI"
- No emoji, hashtags, exclamation points, rhetorical questions, URL shorteners
- No filler openings: "Let's dive in", "In this post", "Buckle up"
- End with the full github.com/... URL

**Channel length limits:**
- Bluesky: 300 characters max (count carefully)
- Mastodon: 500 characters max
- X: 280 characters max
- Dev.to / Hashnode: 150-400 words, prepend `# Title` on first line

Generate 3 candidates for the requested channel. Show all 3.

## Step 3: Validate each candidate

Write each draft to a temp file and validate:

```bash
echo 'draft text here' | marketing validate --channel bluesky
```

If FAILED, fix the violations and revalidate. Only present candidates that PASS to the user.

## Step 4: Save the best one

Save the user's chosen draft to `content/drafts/{project}/{channel}/`.
