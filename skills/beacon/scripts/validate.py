"""Validate .beacon/launch.json (Beacon, phase 6).

    python3 validate.py .beacon/launch.json [--repo .]

Checks the positioning gate, that sources and phrases attributed to people
are real (verbatim quotes are matched against the raw text in
.beacon/sources.jsonl), counts independent authors per pain, and rejects
fake precision (score-like keys). Exit 0 when valid; otherwise prints every
problem and exits 1.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

FIELDS = ("problem", "failure", "product", "proof", "boundary")
PLATFORMS = ("hn", "github", "reddit", "web")
GENERIC_WHO = {"developers", "ai developers", "everyone", "engineers", "users", "developer"}
BANNED = re.compile(r"(^|_)(score|pmf|percent|percentage|probability)($|_)", re.I)
norm = lambda s: re.sub(r"\s+", " ", (s or "")).strip().lower()


def banned_keys(obj, path="") -> list[str]:
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if BANNED.search(k):
                out.append(f"{path}{k}: no scores or percentages; say what was observed")
            out += banned_keys(v, f"{path}{k}.")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out += banned_keys(v, f"{path}[{i}].")
    return out


def locator_ok(ev: dict, repo: Path) -> str | None:
    if ev.get("url"):
        return None
    f = ev.get("file")
    if not f:
        return "needs a file+line or url"
    p = repo / f
    if not p.is_file():
        return f"file not found: {f}"
    line = ev.get("line")
    if line is not None:
        n = sum(1 for _ in p.open(errors="replace"))
        if not (isinstance(line, int) and 1 <= line <= n):
            return f"line {line} out of range for {f} ({n} lines)"
    return None


def independent_authors(pain: dict, by_id: dict) -> int:
    return len({(by_id[s].get("platform"), (by_id[s].get("author") or "").lower())
                for s in pain.get("source_ids", []) if s in by_id})


def validate(doc: dict, repo: Path, raw: dict[str, dict]) -> list[str]:
    errs = banned_keys(doc)
    if doc.get("version") != 1:
        errs.append("version must be 1")
    gate = doc.get("gate")
    if gate not in ("pass", "stop"):
        errs.append("gate must be pass or stop")
    if gate == "stop":
        if not doc.get("gate_missing"):
            errs.append("gate stop: list what is missing in gate_missing")
        if doc.get("experiment"):
            errs.append("gate stop: no experiment until the positioning can be stated")
    pos = doc.get("positioning") or {}
    if gate == "pass":
        for f in FIELDS:
            item = pos.get(f) or {}
            if not (item.get("text") or "").strip():
                errs.append(f"positioning.{f}: missing text")
            evs = item.get("evidence") or []
            if not evs:
                errs.append(f"positioning.{f}: needs evidence")
            for j, ev in enumerate(evs):
                why = locator_ok(ev, repo)
                if why:
                    errs.append(f"positioning.{f}.evidence[{j}]: {why}")

    by_id: dict[str, dict] = {}
    for i, s in enumerate(doc.get("sources") or []):
        w = f"sources[{s.get('id', i)}]"
        if s.get("id") in by_id:
            errs.append(f"{w}: duplicate id")
        by_id[s.get("id")] = s
        if s.get("platform") not in PLATFORMS:
            errs.append(f"{w}: platform must be one of {PLATFORMS}")
        for k in ("url", "author", "date", "quote"):
            if not s.get(k):
                errs.append(f"{w}: missing {k}")
        if not isinstance(s.get("verbatim"), bool):
            errs.append(f"{w}: verbatim must be true or false")
        if s.get("verbatim") and s.get("id") in raw:
            if norm(s.get("quote")) not in norm(raw[s["id"]].get("text")):
                errs.append(f"{w}: marked verbatim but the quote isn't in the source's raw text")

    for i, p in enumerate(doc.get("pains") or []):
        w = f"pain {p.get('id', i)}"
        ids = p.get("source_ids") or []
        if not ids:
            errs.append(f"{w}: needs source_ids")
        for sid in ids:
            if sid not in by_id:
                errs.append(f"{w}: unknown source {sid}")
        if p.get("fit") not in ("high", "partial", "none"):
            errs.append(f"{w}: fit must be high, partial or none")
        if not p.get("fit_reason"):
            errs.append(f"{w}: needs fit_reason")
        for ph in p.get("language") or []:
            src = by_id.get(ph.get("source_id"))
            if not src:
                errs.append(f"{w}: language phrase cites unknown source {ph.get('source_id')}")
            elif src.get("verbatim") and norm(ph.get("text")) not in norm(src.get("quote")) \
                    and norm(ph.get("text")) not in norm(raw.get(src["id"], {}).get("text")):
                errs.append(f"{w}: phrase '{ph.get('text')}' is not in {src['id']}'s words")
        for wk in p.get("workarounds") or []:
            for sid in wk.get("source_ids") or []:
                if sid not in by_id:
                    errs.append(f"{w}: workaround cites unknown source {sid}")
    for c in doc.get("counter_evidence") or []:
        for sid in c.get("source_ids") or []:
            if sid not in by_id:
                errs.append(f"counter_evidence: unknown source {sid}")

    auds = doc.get("audiences") or []
    if gate == "pass" and not 2 <= len(auds) <= 4:
        errs.append("audiences: give 2-4 specific audiences")
    aud_ids = set()
    for a in auds:
        w = f"audience {a.get('id')}"
        aud_ids.add(a.get("id"))
        if norm(a.get("who")) in GENERIC_WHO or len(norm(a.get("who"))) < 12:
            errs.append(f"{w}: 'who' is too generic; name the people and their situation")
        if a.get("fit") not in ("strong", "partial", "weak"):
            errs.append(f"{w}: fit must be strong, partial or weak")
        for sid in a.get("source_ids") or []:
            if sid not in by_id:
                errs.append(f"{w}: unknown source {sid}")

    ex = doc.get("experiment")
    if gate == "pass":
        if not ex:
            errs.append("experiment: a passing gate needs exactly one next experiment")
        else:
            for k in ("audience", "hook", "message", "channel", "cta", "hypothesis", "history_file"):
                if not ex.get(k):
                    errs.append(f"experiment: missing {k}")
            if not isinstance(ex.get("channel"), str):
                errs.append("experiment: channel must be one channel (a string)")
            if ex.get("audience") not in aud_ids:
                errs.append("experiment: audience must be one of the audience ids")
            sc = ex.get("success") or {}
            for k in ("signal", "threshold", "window_hours", "failure"):
                if sc.get(k) in (None, ""):
                    errs.append(f"experiment.success: missing {k}")
            if not ex.get("why_channel"):
                errs.append("experiment: why_channel needs evidence")
            for wc in ex.get("why_channel") or []:
                for sid in wc.get("source_ids") or []:
                    if sid not in by_id:
                        errs.append(f"experiment.why_channel: unknown source {sid}")
            if not ex.get("not_this_round"):
                errs.append("experiment: list what is not this round, with reasons")
    return errs


def summary(doc: dict) -> str:
    by_id = {s["id"]: s for s in doc.get("sources") or [] if "id" in s}
    parts = [f"{p['id']}: {independent_authors(p, by_id)} independent author(s)" for p in doc.get("pains") or []]
    v = sum(1 for s in by_id.values() if s.get("verbatim"))
    return (f"gate {doc.get('gate')}; {len(by_id)} sources ({v} verbatim); "
            + ("; ".join(parts) or "no pains"))


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: validate.py .beacon/launch.json [--repo .]")
        return 2
    path = Path(argv[0])
    repo = Path(argv[argv.index("--repo") + 1]) if "--repo" in argv else path.resolve().parent.parent
    doc = json.loads(path.read_text())
    raw = {}
    jl = path.parent / "sources.jsonl"
    if jl.exists():
        for line in jl.read_text().splitlines():
            if line.strip():
                s = json.loads(line)
                raw[s["id"]] = s
    errs = validate(doc, repo, raw)
    for e in errs:
        print(e)
    if not errs:
        print("ok: " + summary(doc))
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
