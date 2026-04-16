---
name: report
description: "Fetch engagement metrics from all platforms and show how posts are performing. Sends a Slack digest if configured."
user-invocable: true
allowed-tools:
  - Bash(marketing report)
---

# Engagement report

Fetches current likes, reposts, replies, and views from Bluesky, Dev.to, Hashnode, and Mastodon for all tracked posts.

```bash
marketing report
```

Shows:
- Total engagement and views across all posts
- Per-post breakdown sorted by engagement (highest first)
- Top performer highlight

Saves a dated snapshot to `reports/metrics/YYYY-MM-DD.yml` for tracking trends over time.

If `SLACK_WEBHOOK_URL` is configured, sends a formatted digest to Slack.

**Auto-sync:** before fetching, runs `git pull --rebase --autostash` to pick up any new posts the GH Actions cron has committed to `content/posted/manifest.yml`. Without this the local manifest goes stale and the digest under-reports. Pass `--no-sync` to skip (e.g., when running on the cron itself).

When discussing results with the user, highlight which projects/channels/angles are performing best and which aren't getting traction. This is the data that should inform future angle choices.
