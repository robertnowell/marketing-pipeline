"""Publish human-approved posts VERBATIM.

Content derived from private/client sources is generalized and held in the
content-engine review queue; when the operator approves it, the exact post
text lands in content/pre-approved/<id>.json. This posts those texts as-is —
no drafting, no antislop rewrite, no re-identification risk introduced after
approval. Runs first in the daily cycle so approved items go out promptly.

Each file: {id, date, project, angle, posts: [{channel, text}]}.
On success the file is moved to content/pre-approved/posted/ so it never
re-posts.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import re

from pipeline.antislop import PRIVACY_DENYLIST
from pipeline.config import Config, ConfigError
from pipeline.publish import get_publisher
from pipeline.report import add_to_manifest


def _denylist_hit(text: str) -> str | None:
    low = text.lower()
    for ent in PRIVACY_DENYLIST:
        if re.search(r"(?<![a-z0-9])" + re.escape(ent.lower()) + r"(?![a-z0-9])", low):
            return ent
    return None

PREAPPROVED = Path("content/pre-approved")
DONE = PREAPPROVED / "posted"


def _title_from(text: str) -> str | None:
    first = text.strip().split("\n", 1)[0]
    return first.lstrip("# ").strip() if first.startswith("# ") else None


def run(config: Config) -> int:
    if not PREAPPROVED.exists():
        print("no pre-approved queue")
        return 0
    files = sorted(p for p in PREAPPROVED.glob("*.json"))
    if not files:
        print("no approved posts pending")
        return 0
    DONE.mkdir(parents=True, exist_ok=True)
    posted = 0
    for f in files:
        rec = json.loads(f.read_text())
        all_ok = True
        for post in rec.get("posts", []):
            channel, text = post.get("channel"), post.get("text", "")
            if not text.strip():
                continue
            # Final backstop: even operator-approved text can't publish a
            # denylisted private party (guards against human slip on edit).
            hit = _denylist_hit(text)
            if hit:
                print(f"  🔒 {rec['id']} | {channel}: BLOCKED — approved text still "
                      f"names '{hit}'; not posting.", file=sys.stderr)
                all_ok = False
                continue
            try:
                pub = get_publisher(channel)
            except ValueError:
                print(f"  {rec['id']} | no publisher for '{channel}', skipping", file=sys.stderr)
                continue
            try:
                # Long-form channels want a title extracted from the '# ' line.
                if channel in ("devto", "hashnode") and _title_from(text):
                    result = pub.publish(text, config, title=_title_from(text))
                else:
                    result = pub.publish(text, config)
            except ConfigError as e:
                print(f"  {rec['id']} | {channel}: missing creds, skipping ({e})", file=sys.stderr)
                all_ok = False
                continue
            except Exception as e:
                print(f"  {rec['id']} | {channel}: publish error, skipping ({e})", file=sys.stderr)
                all_ok = False
                continue
            if result.success:
                print(f"  Posted (approved): {result.url or result.error}")
                add_to_manifest(project=rec.get("project", "research"), channel=channel,
                                url=result.url or "", angle=rec.get("angle", ""),
                                source_id=rec["id"])
                posted += 1
            else:
                print(f"  {rec['id']} | {channel}: failed — {result.error}", file=sys.stderr)
                all_ok = False
        # Move fully-processed files aside so they don't re-post. If a channel
        # was skipped for missing creds, still move it (it was the operator's
        # approved set; a missing channel isn't a reason to re-post the rest).
        shutil.move(str(f), str(DONE / f.name))
        if not all_ok:
            print(f"  {rec['id']}: some channels did not post (see above)")
    print(f"pre-approved: {posted} post(s) published")
    return 0
