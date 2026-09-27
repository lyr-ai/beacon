"""Validate .beacon/launch.json (Beacon, phase 6).

    python3 validate.py .beacon/launch.json [--repo .]
    python3 validate.py --value .beacon/value.json [--repo .]

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


LEVELS = ("demonstrated", "supported", "hypothesis")


def has_loc(ev: dict) -> bool:
    return bool(ev.get("file") or ev.get("url") or ev.get("commit") or ev.get("issue")
                or ("command" in ev and "exit_code" in ev))


def validate_value(doc: dict, repo: Path, launch: dict | None) -> list[str]:
    errs = banned_keys(doc)
    if doc.get("version") != 1:
        errs.append("version must be 1")
    prob = doc.get("problem") or {}
    if not (prob.get("text") or "").strip():
        errs.append("problem: missing text")
    for j, ev in enumerate(prob.get("evidence") or []):
        why = locator_ok(ev, repo) if ev.get("file") else None
        if why:
            errs.append(f"problem.evidence[{j}]: {why}")
    caps = {}
    for c in doc.get("capabilities") or []:
        w = f"capability {c.get('id')}"
        if not (c.get("id") and c.get("name")):
            errs.append(f"{w}: needs id and name")
        if c.get("id") in caps:
            errs.append(f"{w}: duplicate id")
        caps[c.get("id")] = c
        evs = c.get("evidence") or []
        if not evs:
            errs.append(f"{w}: needs a code or doc locator")
        for j, ev in enumerate(evs):
            why = locator_ok(ev, repo)
            if why:
                errs.append(f"{w}.evidence[{j}]: {why}")
    pains = {p.get("id") for p in (launch or {}).get("pains") or []}
    vals = {}
    for v in doc.get("values") or []:
        w = f"value {v.get('id')}"
        vals[v.get("id")] = v
        for k in ("outcome", "why"):
            if not (v.get(k) or "").strip():
                errs.append(f"{w}: missing {k}")
        lv = v.get("level")
        if lv not in LEVELS:
            errs.append(f"{w}: level must be one of {LEVELS}")
        if not v.get("capabilities"):
            errs.append(f"{w}: name the capabilities that deliver it")
        for c in v.get("capabilities") or []:
            if c not in caps:
                errs.append(f"{w}: unknown capability {c}")
        proof = v.get("proof") or []
        confirmed = [x for x in proof if x.get("level") == "confirmed"]
        for j, x in enumerate(proof):
            if not has_loc(x):
                errs.append(f"{w}.proof[{j}]: needs a locator (file/url/commit/issue/command)")
            elif x.get("file"):
                why = locator_ok(x, repo)
                if why:
                    errs.append(f"{w}.proof[{j}]: {why}")
        if lv == "demonstrated" and not confirmed:
            errs.append(f"{w}: demonstrated needs a confirmed proof (test, benchmark or command output)")
        if lv in ("supported", "hypothesis") and confirmed:
            errs.append(f"{w}: has confirmed proof; call it demonstrated, or remove the proof")
        if launch is not None:
            for pid in v.get("pains") or []:
                if pid not in pains:
                    errs.append(f"{w}: unknown pain {pid} (not in .beacon/launch.json)")
    fs = doc.get("first_screen") or {}
    if fs:
        lead = fs.get("lead") or []
        if len(lead) != 1:
            errs.append("first_screen.lead: exactly one value")
        for vid in lead:
            if vals.get(vid, {}).get("level") == "hypothesis":
                errs.append(f"first_screen.lead: {vid} is a hypothesis; lead with a demonstrated or supported value")
        for part in ("lead", "support", "trust"):
            for vid in fs.get(part) or []:
                if vid not in vals:
                    errs.append(f"first_screen.{part}: unknown value {vid}")
        for a in fs.get("advanced") or []:
            if a.get("capability") not in caps:
                errs.append(f"first_screen.advanced: unknown capability {a.get('capability')}")
            if not a.get("reason"):
                errs.append("first_screen.advanced: each item needs a reason")
        for j, x in enumerate(fs.get("stop_saying") or []):
            if not x.get("reason"):
                errs.append(f"first_screen.stop_saying[{j}]: needs a reason")
            why = locator_ok(x, repo) if (x.get("file") or x.get("url")) else "needs the locator where the claim is made"
            if why:
                errs.append(f"first_screen.stop_saying[{j}]: {why}")
    return errs


def coverage(doc: dict) -> dict[str, list[str]]:
    """capability id -> the value ids it supports (derived, never typed)."""
    cov = {c["id"]: [] for c in doc.get("capabilities") or [] if "id" in c}
    for v in doc.get("values") or []:
        for c in v.get("capabilities") or []:
            cov.setdefault(c, []).append(v.get("id"))
    return cov


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
    if "--value" in argv:
        path = Path(argv[argv.index("--value") + 1])
        repo = Path(argv[argv.index("--repo") + 1]) if "--repo" in argv else path.resolve().parent.parent
        doc = json.loads(path.read_text())
        lp = path.parent / "launch.json"
        errs = validate_value(doc, repo, json.loads(lp.read_text()) if lp.exists() else None)
        for e in errs:
            print(e)
        if not errs:
            vals = doc.get("values") or []
            tally = ", ".join(f"{sum(v.get('level') == l for v in vals)} {l}" for l in LEVELS)
            orphan_caps = [c for c, vs in coverage(doc).items() if not vs]
            no_pain = [v["id"] for v in vals if not v.get("pains")]
            print(f"ok: {len(vals)} values ({tally}); capabilities supporting no value: {orphan_caps or 'none'}; "
                  f"values answering no observed pain: {no_pain or 'none'}")
        return 1 if errs else 0
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
