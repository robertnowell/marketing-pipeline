"""Anti-slop validation gate tests."""

from __future__ import annotations

from pipeline.antislop import validate

# --- Marketing tokens ---

def test_rejects_marketing_tokens() -> None:
    result = validate("We're excited to share our new tool.")
    assert not result.passed
    violations = [v.rule for v in result.hard_failures]
    assert "marketing_token" in violations


def test_rejects_game_changer() -> None:
    result = validate("This is a real game-changer for developers.")
    assert not result.passed


def test_rejects_unlock() -> None:
    result = validate("Unlock the full potential of your workflow.")
    assert not result.passed


def test_rejects_check_it_out() -> None:
    result = validate("Built something neat. Check it out here.")
    assert not result.passed


# --- AI shorthand ---

def test_rejects_ai_powered() -> None:
    result = validate("An AI-powered tool for better translations.")
    assert not result.passed
    violations = [v.rule for v in result.hard_failures]
    assert "ai_shorthand" in violations


def test_rejects_powered_by_ai() -> None:
    result = validate("A translation tool powered by AI models.")
    assert not result.passed


def test_allows_bare_ai_mention() -> None:
    """The word 'AI' alone is fine — only marketing phrasings are blocked."""
    result = validate("The tool uses AI to suggest three register-appropriate options.")
    # AI in first sentence is a soft warning, not a hard failure
    assert result.passed


# --- Emoji and hashtags ---

def test_rejects_emoji() -> None:
    result = validate("Shipped a new tool \U0001f680 for language learning.")
    assert not result.passed
    violations = [v.rule for v in result.hard_failures]
    assert "emoji" in violations


def test_rejects_hashtags() -> None:
    result = validate("Built a new MCP server #buildinpublic #mcp")
    assert not result.passed
    violations = [v.rule for v in result.hard_failures]
    assert "hashtag" in violations


def test_rejects_exclamation_points() -> None:
    result = validate("This tool is great!")
    assert not result.passed
    violations = [v.rule for v in result.hard_failures]
    assert "exclamation" in violations


# --- Filler openings ---

def test_rejects_lets_dive_in() -> None:
    result = validate("Let's dive in to how this tool works.")
    assert not result.passed


def test_rejects_buckle_up() -> None:
    result = validate("Buckle up, here's what I built this week.")
    assert not result.passed


def test_rejects_in_this_post() -> None:
    result = validate("In this post, I'll walk through the architecture.")
    assert not result.passed


# --- Rhetorical questions ---

def test_rejects_rhetorical_question() -> None:
    result = validate("Ever struggled with translating idioms? Here's a fix.")
    assert not result.passed


# --- URL shorteners ---

def test_rejects_url_shorteners() -> None:
    result = validate("Built a tool: https://bit.ly/abc123")
    assert not result.passed


def test_allows_full_github_urls() -> None:
    result = validate(
        "Google Translate gives you one option with no context. "
        "konid returns three, casual to formal. github.com/robertnowell/konid"
    )
    assert result.passed


# --- First-line technology check (soft warning) ---

def test_warns_on_first_line_tech() -> None:
    result = validate("AI makes translation better. konid uses it to give you three options.")
    assert result.passed  # soft warning, not hard failure
    warning_rules = [v.rule for v in result.warnings]
    assert "first_line_tech" in warning_rules


def test_no_warning_when_pain_leads() -> None:
    result = validate(
        "Google Translate gives you one literal translation with no register context. "
        "konid returns three options, casual to formal, with pronunciation."
    )
    assert result.passed
    assert len(result.warnings) == 0


# --- Channel length checks ---

def test_bluesky_length_limit() -> None:
    long_post = "a" * 301
    result = validate(long_post, channel="bluesky")
    assert not result.passed
    violations = [v.rule for v in result.hard_failures]
    assert "length" in violations


def test_bluesky_within_limit() -> None:
    short_post = "Google Translate told me estoy caliente means I'm hot. It doesn't. " * 2
    result = validate(short_post.strip(), channel="bluesky")
    length_violations = [v for v in result.violations if v.rule == "length"]
    # Only check length — other rules may fire depending on content
    if len(short_post.strip()) <= 300:
        assert not length_violations


def test_devto_min_words() -> None:
    short_post = "This is too short for Dev.to."
    result = validate(short_post, channel="devto")
    violations = [v for v in result.hard_failures if v.rule == "length"]
    assert violations


# --- Clean drafts pass ---

def test_clean_short_form_passes() -> None:
    draft = (
        "Google Translate told me 'estoy caliente' means 'I'm hot' in Spanish. "
        "It doesn't. konid returns three options casual-to-formal for anything you "
        "want to say, with the register explained and audio pronunciation. "
        "github.com/robertnowell/konid"
    )
    result = validate(draft, channel="bluesky")
    assert result.passed, f"Clean draft failed: {[v.detail for v in result.violations]}"


def test_clean_long_form_passes() -> None:
    draft = (
        "Google Translate gives you one literal translation with no register context. "
        "Say 'I'm hot' in Spanish and you get 'estoy caliente' -- which means "
        "'I'm sexually aroused,' not 'I'm warm.' The tool has no awareness of who "
        "you're talking to, whether the situation is casual or formal, or whether "
        "the phrase is idiomatic. Korean has built-in politeness levels where a "
        "verb like 'to go' can be plain, polite, or honorific, and Google picks "
        "the middle option every time.\n\n"
        "konid is an MCP server that returns three expression options for anything "
        "you want to say in another language -- casual, standard, and formal -- "
        "with the register explained and audio pronunciation for each. It works "
        "inside Claude Code, Cursor, or any MCP-compatible client. You type what "
        "you want to say in English, pick the target language, and get back three "
        "options ranked by formality.\n\n"
        "The difference: instead of one literal answer you have to trust blindly, "
        "you get three options with enough context to pick the right one. Each "
        "option includes a register label (casual, standard, formal), a brief "
        "explanation of when to use it, and audio pronunciation so you can hear "
        "how a native speaker would say it. "
        "Supports 13+ languages. Open source.\n\n"
        "github.com/robertnowell/konid"
    )
    result = validate(draft, channel="devto")
    assert result.passed, f"Clean long draft failed: {[v.detail for v in result.violations]}"
