"""Blind cold-read judge for long-form titles.

Simulates the feed: the judge sees ONLY the titles and the audience — never
the body — because a judge that can see the body confabulates context the
real cold reader doesn't have (the two-phase lesson from the video
pipeline's thumbnail/script judges).

A title passes only if a stranger in the audience can tell, from the title
alone: (a) what subject domain the post is about, and (b) why it's worth a
click. Failures come back as reasons, which the drafter's retry loop feeds
back to the model.
"""
from __future__ import annotations

import json
import re

import anthropic

JUDGE_SYSTEM = """You are a cold reader scrolling a feed. You will be given \
post titles and a description of who you are (the audience). You know NOTHING \
except each title itself — no body, no context, no memory of other posts.

For each title, answer honestly:
1. subject: what is this post about, concretely? If you cannot name the \
subject domain (e.g. "blog posts", "email marketing", "used Teslas"), say \
"unclear".
2. click: would you, as this audience member, click? A title earns a click \
only if you can tell what it's about AND something surprising or useful is \
at stake for you. Undefined references ("this rule", "the gate", unnamed \
"experts"), missing subject domains, and insider names you don't recognize \
are all reasons not to click.
3. verdict: "pass" only if subject is clear AND you would click. Otherwise \
"fail" with the reason a real reader would give ("no idea what rule this \
means", "who is this person", "what does this apply to").

Return ONLY a JSON array, one object per title, in order:
[{"subject": "...", "verdict": "pass"|"fail", "reason": "..."}]"""


def extract_title(draft: str) -> str | None:
    first_line = draft.strip().split("\n", 1)[0]
    if first_line.startswith("# "):
        return first_line.lstrip("# ").strip()
    return None


def judge_titles(
    client: anthropic.Anthropic,
    titles: list[str],
    audience: str,
    model: str = "claude-sonnet-4-6",
) -> list[dict]:
    """Return one {"verdict", "reason", "subject"} per title, in order.

    Fails open: on any API/parse error, every title passes — the judge is a
    quality gate, not an availability dependency.
    """
    if not titles:
        return []
    user = json.dumps({"audience": audience, "titles": titles})
    try:
        resp = client.messages.create(
            model=model,
            max_tokens=1024,
            system=JUDGE_SYSTEM,
            messages=[{"role": "user", "content": user}],
        )
        text = resp.content[0].text.strip()
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
        verdicts = json.loads(text)
        if isinstance(verdicts, list) and len(verdicts) == len(titles):
            return verdicts
    except Exception:
        pass
    return [{"verdict": "pass", "reason": "judge unavailable", "subject": ""}
            for _ in titles]
