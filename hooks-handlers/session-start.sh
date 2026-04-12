#!/usr/bin/env bash
# Marketing Pipeline — SessionStart hook
# Creates/updates Python venv, bridges credentials, initializes state.
set -euo pipefail

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:?CLAUDE_PLUGIN_ROOT not set}"
PLUGIN_DATA="${CLAUDE_PLUGIN_DATA:?CLAUDE_PLUGIN_DATA not set}"

VENV_DIR="$PLUGIN_DATA/venv"
STATE_DIR="$PLUGIN_DATA/state"
HASH_FILE="$PLUGIN_DATA/.deps-hash"

# --- 1. Python version check ---
PYTHON_VERSION=$(python3 --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+' | head -1)
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ -z "$PYTHON_VERSION" ] || [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 12 ]; }; then
  echo '{"hookSpecificOutput":{"additionalContext":"ERROR: Python 3.12+ is required but not found. Install Python 3.12+ and restart."}}' >&2
  exit 1
fi

# --- 2. Venv + dependency installation (hash-gated) ---
CURRENT_HASH=$(shasum -a 256 "$PLUGIN_ROOT/pyproject.toml" 2>/dev/null | cut -d' ' -f1 || echo "none")
CACHED_HASH=""
if [ -f "$HASH_FILE" ]; then
  CACHED_HASH=$(cat "$HASH_FILE")
fi

if [ "$CURRENT_HASH" != "$CACHED_HASH" ] || [ ! -d "$VENV_DIR/bin" ]; then
  echo "Marketing pipeline: installing dependencies..." >&2
  python3 -m venv "$VENV_DIR" 2>/dev/null || true
  "$VENV_DIR/bin/pip" install --quiet --disable-pip-version-check "$PLUGIN_ROOT" 2>/dev/null
  echo "$CURRENT_HASH" > "$HASH_FILE"
fi

# --- 3. Initialize state directory (first run only) ---
if [ ! -d "$STATE_DIR" ]; then
  mkdir -p "$STATE_DIR"
  cp "$PLUGIN_ROOT/defaults/projects.yml" "$STATE_DIR/projects.yml" 2>/dev/null || true
  cp "$PLUGIN_ROOT/defaults/surfaces.yml" "$STATE_DIR/surfaces.yml" 2>/dev/null || true
  mkdir -p "$STATE_DIR/content/drafts" "$STATE_DIR/content/posted" "$STATE_DIR/reports/metrics"
  # Copy prompts for the drafter (it resolves via the installed package, but keep a reference copy)
fi

# --- 4. Bridge credentials to standard env var names ---
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  {
    # Required
    [ -n "${CLAUDE_PLUGIN_OPTION_ANTHROPIC_API_KEY:-}" ] && \
      echo "export ANTHROPIC_API_KEY=\"${CLAUDE_PLUGIN_OPTION_ANTHROPIC_API_KEY}\""
    [ -n "${CLAUDE_PLUGIN_OPTION_BLUESKY_HANDLE:-}" ] && \
      echo "export BLUESKY_HANDLE=\"${CLAUDE_PLUGIN_OPTION_BLUESKY_HANDLE}\""
    [ -n "${CLAUDE_PLUGIN_OPTION_BLUESKY_APP_PASSWORD:-}" ] && \
      echo "export BLUESKY_APP_PASSWORD=\"${CLAUDE_PLUGIN_OPTION_BLUESKY_APP_PASSWORD}\""
    [ -n "${CLAUDE_PLUGIN_OPTION_DEVTO_API_KEY:-}" ] && \
      echo "export DEVTO_API_KEY=\"${CLAUDE_PLUGIN_OPTION_DEVTO_API_KEY}\""

    # Optional
    [ -n "${CLAUDE_PLUGIN_OPTION_HASHNODE_PAT:-}" ] && \
      echo "export HASHNODE_PAT=\"${CLAUDE_PLUGIN_OPTION_HASHNODE_PAT}\""
    [ -n "${CLAUDE_PLUGIN_OPTION_HASHNODE_PUBLICATION_ID:-}" ] && \
      echo "export HASHNODE_PUBLICATION_ID=\"${CLAUDE_PLUGIN_OPTION_HASHNODE_PUBLICATION_ID}\""
    [ -n "${CLAUDE_PLUGIN_OPTION_MASTODON_ACCESS_TOKEN:-}" ] && \
      echo "export MASTODON_ACCESS_TOKEN=\"${CLAUDE_PLUGIN_OPTION_MASTODON_ACCESS_TOKEN}\""
    [ -n "${CLAUDE_PLUGIN_OPTION_MASTODON_INSTANCE_URL:-}" ] && \
      echo "export MASTODON_INSTANCE_URL=\"${CLAUDE_PLUGIN_OPTION_MASTODON_INSTANCE_URL}\""
    [ -n "${CLAUDE_PLUGIN_OPTION_SLACK_WEBHOOK_URL:-}" ] && \
      echo "export SLACK_WEBHOOK_URL=\"${CLAUDE_PLUGIN_OPTION_SLACK_WEBHOOK_URL}\""

    # State directory for the bin/marketing wrapper
    echo "export MARKETING_STATE_DIR=\"${STATE_DIR}\""
  } >> "$CLAUDE_ENV_FILE"
fi

# --- 5. Report status ---
PROJECT_COUNT=0
POST_COUNT=0
if [ -f "$STATE_DIR/projects.yml" ]; then
  PROJECT_COUNT=$(grep -c "^[a-z]" "$STATE_DIR/projects.yml" 2>/dev/null || echo "0")
fi
if [ -f "$STATE_DIR/content/posted/manifest.yml" ]; then
  POST_COUNT=$(grep -c "^- project:" "$STATE_DIR/content/posted/manifest.yml" 2>/dev/null || echo "0")
fi

echo "{\"hookSpecificOutput\":{\"additionalContext\":\"Marketing pipeline ready: ${PROJECT_COUNT} projects, ${POST_COUNT} posts tracked. Use /onboard to add a project, /status to see current state.\"}}"
