"""Interactive setup checker and guide.

Checks which credentials are configured, which platforms are reachable,
and prints exactly what's missing with links to fix it.
"""

from __future__ import annotations

import os
from pathlib import Path

import httpx

from pipeline.config import Config

# Each check: (name, env_vars_needed, setup_url, instructions)
CHECKS = [
    {
        "name": "Anthropic API (drafting)",
        "env": ["ANTHROPIC_API_KEY"],
        "url": "https://console.anthropic.com/settings/keys",
        "how": "Create an API key. Paste into .env as ANTHROPIC_API_KEY=sk-ant-...",
        "required": True,
    },
    {
        "name": "Bluesky (posting)",
        "env": ["BLUESKY_HANDLE", "BLUESKY_APP_PASSWORD"],
        "url": "https://bsky.app/settings → Privacy and security → App Passwords",
        "how": "Create an app password. Set BLUESKY_HANDLE and BLUESKY_APP_PASSWORD in .env",
        "required": True,
    },
    {
        "name": "Dev.to (posting)",
        "env": ["DEVTO_API_KEY"],
        "url": "https://dev.to/settings/extensions",
        "how": "Scroll to 'DEV Community API Keys', generate one. Set DEVTO_API_KEY in .env",
        "required": True,
    },
    {
        "name": "Hashnode (posting)",
        "env": ["HASHNODE_PAT", "HASHNODE_PUBLICATION_ID"],
        "url": "https://hashnode.com → Avatar → Account Settings → Developer",
        "how": (
            "Generate a Personal Access Token. For publication ID, run:\n"
            "    curl -s -X POST https://gql.hashnode.com \\\n"
            "      -H 'Authorization: YOUR_PAT' \\\n"
            "      -H 'Content-Type: application/json' \\\n"
            "      -d '{\"query\": \"{ me { publications(first:5) { edges { node { id title url } } } } }\"}'\n"
            "Set HASHNODE_PAT and HASHNODE_PUBLICATION_ID in .env"
        ),
        "required": True,
    },
    {
        "name": "Mastodon (posting)",
        "env": ["MASTODON_ACCESS_TOKEN", "MASTODON_INSTANCE_URL"],
        "url": "https://YOUR-INSTANCE/settings/applications",
        "how": (
            "Pick an instance (hachyderm.io, fosstodon.org, mastodon.social).\n"
            "Go to Preferences → Development → New Application.\n"
            "Name: marketing-pipeline, scope: write:statuses.\n"
            "Copy the access token. Set MASTODON_ACCESS_TOKEN and MASTODON_INSTANCE_URL in .env"
        ),
        "required": False,
    },
    {
        "name": "Slack (engagement reports)",
        "env": ["SLACK_WEBHOOK_URL"],
        "url": "https://api.slack.com/apps",
        "how": (
            "Create New App → From scratch → name it → select workspace.\n"
            "Go to Incoming Webhooks → Activate → Add New Webhook to Workspace.\n"
            "Pick a channel, copy the URL. Set SLACK_WEBHOOK_URL in .env"
        ),
        "required": False,
    },
    {
        "name": "npm (package publishing)",
        "env": [],
        "url": "https://www.npmjs.com/settings/~/tokens",
        "how": "Run: npm login\nFor CI, generate an access token and set NPM_TOKEN in GitHub Actions secrets.",
        "required": False,
        "check_cmd": "npm whoami",
    },
]


def run_setup() -> int:
    """Check all credentials and print status."""
    config = Config.from_env()

    print("Marketing Pipeline — Setup Check\n")

    # Check .env exists
    env_path = Path(".env")
    if not env_path.exists():
        print("  No .env file found. Copy .env.example to .env and fill in credentials:")
        print("    cp .env.example .env\n")

    passed = 0
    failed = 0
    optional_missing = 0

    for check in CHECKS:
        name = check["name"]
        required = check.get("required", True)

        # Check env vars
        if check["env"]:
            missing = [v for v in check["env"] if not os.environ.get(v)]
            if missing:
                marker = "X" if required else "-"
                label = "MISSING" if required else "OPTIONAL"
                print(f"  [{marker}] {name} — {label}")
                print(f"      Set: {', '.join(missing)}")
                print(f"      Go to: {check['url']}")
                print(f"      How: {check['how']}")
                print()
                if required:
                    failed += 1
                else:
                    optional_missing += 1
                continue

        # Check special commands (npm)
        if check.get("check_cmd"):
            import subprocess

            result = subprocess.run(
                check["check_cmd"], shell=True, capture_output=True, text=True
            )
            if result.returncode != 0:
                print(f"  [-] {name} — NOT LOGGED IN")
                print(f"      How: {check['how']}")
                print()
                optional_missing += 1
                continue

        print(f"  [ok] {name}")
        passed += 1

    print(f"\n  {passed} configured, {failed} missing (required), {optional_missing} optional")

    if failed > 0:
        print(f"\n  Fix the {failed} required items above to use the pipeline.")
        return 1

    if passed >= 4:
        print("\n  Ready to go. Try:")
        print("    marketing onboard --name my-tool --repo owner/repo --kind mcp-server")
        print("    marketing draft --project my-tool --channel bluesky")

    # Verify connectivity for configured services
    print("\n  Connectivity checks:")
    if config.bluesky:
        try:
            resp = httpx.get(
                "https://public.api.bsky.app/xrpc/com.atproto.identity.resolveHandle",
                params={"handle": config.bluesky.handle},
                timeout=5,
            )
            if resp.status_code == 200:
                print(f"    [ok] Bluesky — handle {config.bluesky.handle} resolves")
            else:
                print(f"    [!]  Bluesky — handle {config.bluesky.handle} not found")
        except Exception:
            print("    [!]  Bluesky — can't reach API")

    if config.devto:
        try:
            resp = httpx.get(
                "https://dev.to/api/users/me",
                headers={"api-key": config.devto.api_key},
                timeout=5,
            )
            if resp.status_code == 200:
                user = resp.json()
                print(f"    [ok] Dev.to — logged in as {user.get('username', '?')}")
            else:
                print("    [!]  Dev.to — API key invalid")
        except Exception:
            print("    [!]  Dev.to — can't reach API")

    if config.anthropic_api_key:
        print("    [ok] Anthropic — key present (not tested to save quota)")

    return 0
