---
name: setup
description: "Check credential configuration and API connectivity."
user-invocable: true
allowed-tools:
  - Bash(marketing setup)
---

# Setup check

Verify that all credentials are configured and APIs are reachable.

```bash
marketing setup
```

Shows which credentials are present, which are missing, and tests connectivity to Bluesky and Dev.to APIs.

In the plugin context, credentials are managed via Claude Code's plugin configuration (stored in the system keychain). If credentials are missing, guide the user to update their plugin settings.
