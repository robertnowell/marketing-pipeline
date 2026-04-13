"""Anti-slop validation gate.

Enforces the voice standard from prompts/draft_post.md as a programmatic check.
Every draft must pass validate() before it reaches a publisher.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# --- Forbidden token lists (extracted from prompts/draft_post.md) ---

MARKETING_TOKENS = [
    r"\bexcited\b",
    r"\bthrilled\b",
    r"\bintroducing\b",
    r"\bgame[- ]?changer\b",
    r"\bsolution\b",
    r"\bfuture of\b",
    r"\bleverage\b",
    r"\bunlock\b",
    r"\bempower\b",
    r"\bjourney\b",
    r"\bcheck it out\b",
    r"\blink in bio\b",
]

AI_SHORTHAND = [
    r"\bAI[- ]?powered\b",
    r"\bAI[- ]?driven\b",
    r"\bpowered by AI\b",
    r"\bnext[- ]?generation AI\b",
    r"\bAI[- ]?first\b",
]

FILLER_OPENINGS = [
    r"^let'?s dive in",
    r"^buckle up",
    r"^in this (video|post|article)",
    r"^as you may know",
    r"^let me walk you through",
    r"^ever struggled with",
    r"^you'?re not alone",
]

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002702-\U000027B0"  # dingbats
    "\U0001F900-\U0001F9FF"  # supplemental
    "\U0001FA00-\U0001FA6F"  # chess
    "\U0001FA70-\U0001FAFF"  # extended-A
    "]+",
    # NOTE: The old U+24C2-U+1F251 range was removed — it spans CJK,
    # Hiragana, Katakana, and Hangul blocks, causing false positives on
    # Japanese/Chinese/Korean text in konid drafts.
)

HASHTAG_PATTERN = re.compile(r"#\w+")

# Rhetorical question at sentence start: "Ever ...?", "Have you ...?", "Want to ...?"
RHETORICAL_Q_PATTERN = re.compile(
    r"(?:^|\. )(Ever |Have you |Want to |Tired of |Struggling with ).*\?", re.IGNORECASE
)

# URL shorteners
URL_SHORTENER_PATTERN = re.compile(
    r"https?://(bit\.ly|t\.co|goo\.gl|tinyurl\.com|ow\.ly|is\.gd|buff\.ly)/",
    re.IGNORECASE,
)

# Technology keywords that should not appear as value props in the first sentence
TECH_KEYWORDS = [
    r"\bAI\b",
    r"\bLLM\b",
    r"\bmachine learning\b",
    r"\bblockchain\b",
    r"\bWebGPU\b",
    r"\bRust\b",
    r"\bGPT\b",
    r"\bClaude\b",
    r"\bneural\b",
]


def _is_quoted(text: str, pos: int) -> bool:
    """Check if the character at pos is inside quotes, backticks, or a code block.

    Allows marketing tokens to appear when quoted — e.g., describing what
    the anti-slop gate blocks: "rejects 'excited' and 'game-changer'".
    Also allows tokens inside ```code blocks``` and inline `code`.
    """
    # Check immediately adjacent quote characters
    before_char = text[pos - 1] if pos > 0 else ""
    # Look in a window around the match position
    window = 40
    chunk_before = text[max(0, pos - window):pos]
    chunk_after = text[pos:min(len(text), pos + window)]

    # Single quotes, double quotes, backticks
    for q in ("'", '"', "`"):
        if before_char == q and q in chunk_after:
            return True
        # Check for enclosing quotes within the window
        if q in chunk_before and q in chunk_after:
            return True

    # Check if inside a fenced code block (``` ... ```)
    text_before = text[:pos]
    fence_opens = text_before.count("```")
    if fence_opens % 2 == 1:
        # Odd number of ``` before this position = we're inside a code block
        return True

    # Check if the line starts with code-block-like patterns (indented code, list of tokens)
    line_start = text_before.rfind("\n", 0, pos)
    line = text[line_start + 1:pos + 20] if line_start >= 0 else text[:pos + 20]
    if line.lstrip().startswith(("r'", "r\"", ">>>", "...")):
        return True

    return False


@dataclass
class Violation:
    rule: str
    detail: str
    severity: str = "hard"  # "hard" = must reject, "soft" = warn


@dataclass
class ValidationResult:
    passed: bool
    violations: list[Violation] = field(default_factory=list)

    @property
    def hard_failures(self) -> list[Violation]:
        return [v for v in self.violations if v.severity == "hard"]

    @property
    def warnings(self) -> list[Violation]:
        return [v for v in self.violations if v.severity == "soft"]


def validate(draft: str, channel: str | None = None) -> ValidationResult:
    """Run the full anti-slop gate on a draft.

    Returns a ValidationResult. The draft passes only if there are zero
    hard violations.
    """
    violations: list[Violation] = []
    text_lower = draft.lower()

    # 1. Marketing tokens (skip matches inside quotes — allows describing what the tool blocks)
    for pattern in MARKETING_TOKENS:
        for match in re.finditer(pattern, text_lower):
            if not _is_quoted(draft, match.start()):
                violations.append(Violation(
                    rule="marketing_token",
                    detail=f"Forbidden marketing token: '{match.group()}'",
                ))
                break  # one violation per pattern is enough

    # 2. AI shorthand (same quoting exception)
    for pattern in AI_SHORTHAND:
        for match in re.finditer(pattern, draft, re.IGNORECASE):
            if not _is_quoted(draft, match.start()):
                violations.append(Violation(
                    rule="ai_shorthand",
                    detail=f"Forbidden AI shorthand: '{match.group()}'",
                ))
                break

    # 3. Emoji
    match = EMOJI_PATTERN.search(draft)
    if match:
        violations.append(Violation(
            rule="emoji",
            detail=f"Emoji not allowed: '{match.group()}'",
        ))

    # 4. Hashtags
    match = HASHTAG_PATTERN.search(draft)
    if match:
        violations.append(Violation(
            rule="hashtag",
            detail=f"Hashtag not allowed: '{match.group()}'",
        ))

    # 5. Exclamation points
    if "!" in draft:
        violations.append(Violation(
            rule="exclamation",
            detail="Exclamation points not allowed",
        ))

    # 6. Filler openings
    first_line = draft.strip().split("\n")[0].lower()
    for pattern in FILLER_OPENINGS:
        if re.search(pattern, first_line):
            violations.append(Violation(
                rule="filler_opening",
                detail=f"Filler opening detected: '{first_line[:60]}...'",
            ))

    # 7. Rhetorical questions
    match = RHETORICAL_Q_PATTERN.search(draft)
    if match:
        violations.append(Violation(
            rule="rhetorical_question",
            detail=f"Rhetorical question: '{match.group()[:60]}'",
        ))

    # 8. URL shorteners
    match = URL_SHORTENER_PATTERN.search(draft)
    if match:
        violations.append(Violation(
            rule="url_shortener",
            detail=f"URL shortener not allowed: '{match.group()}'",
        ))

    # 9. First-line technology check: the opening sentence should not lead
    #    with a technology keyword as a value proposition.
    first_sentence = _first_sentence(draft)
    for pattern in TECH_KEYWORDS:
        match = re.search(pattern, first_sentence)
        if match:
            violations.append(Violation(
                rule="first_line_tech",
                detail=f"First sentence leads with technology: '{match.group()}' in '{first_sentence[:80]}'",
                severity="soft",
            ))

    # 10. Bare domain without https:// (links won't be clickable)
    bare_domain = re.search(
        r"(?<!\w)(?:trykopi\.ai|github\.com|dev\.to|hashnode\.dev)[/\w.-]*",
        draft,
    )
    if bare_domain:
        # Check it's not already preceded by https://
        start = bare_domain.start()
        prefix = draft[max(0, start - 8):start]
        if "://" not in prefix:
            violations.append(Violation(
                rule="bare_domain",
                detail=f"URL missing https:// — won't be clickable: '{bare_domain.group()}'",
                severity="soft",
            ))

    # 11. Channel-specific length checks
    if channel:
        length_violations = _check_length(draft, channel)
        violations.extend(length_violations)

    return ValidationResult(
        passed=not any(v.severity == "hard" for v in violations),
        violations=violations,
    )


def _first_sentence(text: str) -> str:
    """Extract the first sentence from a draft."""
    text = text.strip()
    # Split on period, question mark, or newline — whichever comes first.
    for i, ch in enumerate(text):
        if ch in ".?\n" and i > 10:
            return text[: i + 1]
    return text[:200]


# Character/word limits per channel (from prompts/draft_post.md)
CHANNEL_LIMITS: dict[str, dict[str, int]] = {
    "bluesky": {"max_chars": 300},
    "mastodon": {"max_chars": 500},
    "threads": {"max_chars": 500},
    "x": {"max_chars": 280},
    "devto": {"min_words": 150, "max_words": 400},
    "hashnode": {"min_words": 150, "max_words": 400},
    "indiehackers": {"min_words": 200, "max_words": 600},
}


def _check_length(draft: str, channel: str) -> list[Violation]:
    limits = CHANNEL_LIMITS.get(channel.lower())
    if not limits:
        return []
    violations = []
    char_count = len(draft)
    word_count = len(draft.split())
    if "max_chars" in limits and char_count > limits["max_chars"]:
        violations.append(Violation(
            rule="length",
            detail=f"{channel}: {char_count} chars exceeds {limits['max_chars']} limit",
        ))
    if "min_words" in limits and word_count < limits["min_words"]:
        violations.append(Violation(
            rule="length",
            detail=f"{channel}: {word_count} words below {limits['min_words']} minimum",
        ))
    if "max_words" in limits and word_count > limits["max_words"]:
        violations.append(Violation(
            rule="length",
            detail=f"{channel}: {word_count} words exceeds {limits['max_words']} limit",
        ))
    return violations
