"""Collect public pain evidence with verbatim text (Beacon, phase 3).

    python3 search.py "agent memory outdated facts" "memory conflicting facts" \
        [--since 2025-01-01] [--per-query 15] >> .beacon/sources.jsonl

Queries Hacker News (Algolia API: stories and comments) and GitHub issues
(`gh api search/issues`). Both return the author's own text, so every quote
here is **verbatim**. That is the point of this script: pain evidence is
people's own words, not a model's paraphrase of them.

Each line printed is one JSON source:
  {"id", "platform", "url", "author", "date", "title", "text", "query", "verbatim": true}

Standard library + `gh` (optional; GitHub is skipped without it). Other
platforms (Reddit, blogs) are found with the agent's web search and recorded
by hand in launch.json with "verbatim": false, unless the text was copied
exactly.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

UA = {"User-Agent": "beacon-research/0.1 (+https://github.com/lyr-ai/beacon)"}
TAG = re.compile(r"<[^>]+>")


def clean(s: str | None, limit: int = 1200) -> str:
    s = html.unescape(TAG.sub(" ", s or ""))
    return re.sub(r"\s+", " ", s).strip()[:limit]


def sid(url: str) -> str:
    return hashlib.sha1(url.encode()).hexdigest()[:10]


def hn(query: str, since: int | None, n: int) -> list[dict]:
    params = {"query": query, "tags": "(story,comment)", "hitsPerPage": n}
    if since:
        params["numericFilters"] = f"created_at_i>{since}"
    url = "https://hn.algolia.com/api/v1/search?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
            hits = json.load(r).get("hits", [])
    except OSError as e:
        print(f"hn: {e}", file=sys.stderr)
        return []
    out = []
    for h in hits:
        link = f"https://news.ycombinator.com/item?id={h['objectID']}"
        text = clean(h.get("comment_text") or h.get("story_text") or h.get("title"))
        if not text:
            continue
        out.append({"id": "hn-" + h["objectID"], "platform": "hn", "url": link,
                    "author": h.get("author"), "date": (h.get("created_at") or "")[:10],
                    "title": clean(h.get("title") or h.get("story_title"), 200),
                    "text": text, "query": query, "verbatim": True})
    return out


def github(query: str, since: str | None, n: int) -> list[dict]:
    q = f"{query} is:issue" + (f" created:>{since}" if since else "")
    try:
        p = subprocess.run(["gh", "api", "-X", "GET", "search/issues", "-f", f"q={q}", "-f", f"per_page={n}"],
                           capture_output=True, text=True, timeout=40)
    except (OSError, subprocess.TimeoutExpired) as e:
        print(f"github: {e}", file=sys.stderr)
        return []
    if p.returncode != 0:
        print(f"github: {p.stderr.strip()[:200]}", file=sys.stderr)
        return []
    out = []
    for it in json.loads(p.stdout).get("items", []):
        repo = it["repository_url"].split("/repos/")[-1]
        out.append({"id": "gh-" + sid(it["html_url"]), "platform": "github", "url": it["html_url"],
                    "author": it["user"]["login"], "date": it["created_at"][:10],
                    "title": clean(it["title"], 200), "repo": repo,
                    "text": clean((it.get("title") or "") + ". " + (it.get("body") or "")),
                    "comments": it.get("comments", 0), "query": query, "verbatim": True})
    return out


def main(argv: list[str]) -> int:
    since = argv[argv.index("--since") + 1] if "--since" in argv else None
    n = int(argv[argv.index("--per-query") + 1]) if "--per-query" in argv else 15
    queries = [a for i, a in enumerate(argv) if not a.startswith("--")
               and (i == 0 or argv[i - 1] not in ("--since", "--per-query"))]
    if not queries:
        print(__doc__.strip().splitlines()[2].strip(), file=sys.stderr)
        return 2
    since_ts = int(datetime.fromisoformat(since).replace(tzinfo=timezone.utc).timestamp()) if since else None
    seen = set()
    for q in queries:
        for s in hn(q, since_ts, n) + github(q, since, n):
            if s["url"] in seen:
                continue
            seen.add(s["url"])
            print(json.dumps(s, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
