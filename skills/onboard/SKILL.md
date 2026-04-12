---
name: onboard
description: "Add a new open source project to the marketing pipeline. Researches real user pain first, then generates problem statement, facts, and content angles grounded in that research."
user-invocable: true
allowed-tools:
  - Bash(marketing *)
  - WebSearch
  - WebFetch
  - Write
  - Read
---

# Onboard a new project

This is a multi-step process. Do NOT skip the research phase.

## Step 1: Gather inputs

Ask the user for:
1. **Repository** — GitHub `owner/repo`
2. **Kind** — `mcp-server`, `claude-skill`, `browser-extension`, `terminal-theme`, `cli-audit-tool`, `consumer-web-app`, `b2b-saas`
3. **Audience** (optional, defaults to `claude-code-users`)

## Step 2: Research real user pain

Before generating any marketing content, research how real people describe the problem this tool solves. This is the most important step — it grounds every future post in language that resonates.

1. Read the repo's README to understand what problem the tool addresses
2. Use WebSearch with 3-5 queries to find real complaints about this problem on:
   - Hacker News (search via hn.algolia.com)
   - Reddit (r/programming, r/webdev, relevant subreddits)
   - Dev forums, Stack Overflow, blog comments
3. Use WebFetch to read the most promising 2-3 threads
4. Extract 10-15 **exact quotes** from real users describing their frustration
5. Note the specific vocabulary they use — "awkward", "broken", "waste of time", etc.

Save the research findings to a temp file:

```bash
# Write findings to a temp file
```

Write the file at `/tmp/pain-research-{project-name}.md` with the format:
```
## Pain statements from real users

1. "exact quote" — source (HN/Reddit/forum), engagement (upvotes/comments)
2. "exact quote" — source
...

## Key vocabulary patterns
- words and phrases users reach for when describing this problem
```

## Step 3: Run the onboard command with research context

```bash
marketing onboard --name <name> --repo <owner/repo> --kind <kind> --pain-context /tmp/pain-research-<name>.md
```

This feeds the research into the generation prompt so the problem statement and angles use real user language, not README paraphrasing.

## Step 4: Review the output

Show the user the generated problem, solution, facts, and angles. Call out which pain statements from the research influenced the framing. Suggest edits if any angle feels generic.

Then suggest next steps:
- `marketing draft --project <name> --channel bluesky` to see a sample post
- `marketing launch --project <name> --dry-run` to preview the directory listing plan
