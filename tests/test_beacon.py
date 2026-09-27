"""Beacon's scripts: verbatim collection, the validator's evidence rules, the renderer."""

import copy
import json
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "beacon" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import render  # noqa: E402
import search  # noqa: E402
import validate  # noqa: E402

EX = json.loads((Path(__file__).parent / "example_launch.json").read_text())


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "README.md").write_text("line\n" * 300)
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_state.py").write_text("x\n" * 300)
    (tmp_path / "design").mkdir()
    (tmp_path / "design" / "0002-changing-facts.md").write_text("x\n" * 300)
    return tmp_path


def raw_of(doc):
    return {s["id"]: {"id": s["id"], "text": "prefix " + s["quote"] + " suffix"} for s in doc["sources"]}


def errs(doc, repo, raw=None):
    return validate.validate(doc, repo, raw_of(doc) if raw is None else raw)


# ── search.py ───────────────────────────────────────────────────────────
def test_clean_strips_html_and_entities():
    assert search.clean("<p>I&#x27;ve  had\n to <i>disable</i> it</p>") == "I've had to disable it"


def test_hn_parsing(monkeypatch):
    class R:
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def read(self): return b""
    payload = {"hits": [{"objectID": "1", "author": "a", "created_at": "2026-01-02T00:00:00Z",
                         "comment_text": "Old facts keep &quot;coming back&quot;", "story_title": "Ask HN"},
                        {"objectID": "2", "author": "b", "created_at": "2026-01-03T00:00:00Z"}]}
    monkeypatch.setattr(search.urllib.request, "urlopen", lambda *a, **k: R())
    monkeypatch.setattr(search.json, "load", lambda r: payload)
    out = search.hn("q", None, 5)
    assert [(s["id"], s["text"], s["verbatim"]) for s in out] == [("hn-1", 'Old facts keep "coming back"', True)]


# ── validator ───────────────────────────────────────────────────────────
def test_example_is_valid(repo):
    assert errs(EX, repo) == []


def test_verbatim_quote_must_be_in_raw_text(repo):
    d = copy.deepcopy(EX)
    d["sources"][0]["quote"] = "words nobody wrote"
    raw = raw_of(EX)
    assert any("isn't in the source's raw text" in e for e in errs(d, repo, raw))


def test_paraphrase_is_allowed_when_labelled(repo):
    d = copy.deepcopy(EX)
    d["sources"][0]["quote"] = "a paraphrase"
    d["sources"][0]["verbatim"] = False
    d["pains"] = [dict(p, language=[l for l in p["language"] if l["source_id"] != d["sources"][0]["id"]]) for p in d["pains"]]
    assert errs(d, repo, raw_of(EX)) == []


def test_language_phrase_must_be_the_sources_words(repo):
    d = copy.deepcopy(EX)
    d["pains"][0]["language"][0]["text"] = "invented phrase"
    assert any("is not in" in e for e in errs(d, repo))


def test_independent_authors_are_counted_not_typed():
    by_id = {s["id"]: s for s in EX["sources"]}
    p = dict(EX["pains"][0], source_ids=[EX["sources"][0]["id"], EX["sources"][0]["id"]])
    assert validate.independent_authors(p, by_id) == 1


@pytest.mark.parametrize("mutate,needle", [
    (lambda d: d["positioning"]["proof"].update(evidence=[]), "positioning.proof: needs evidence"),
    (lambda d: d["positioning"]["problem"]["evidence"].__setitem__(0, {"file": "README.md", "line": 999}), "out of range"),
    (lambda d: d["audiences"][0].update(who="AI developers"), "too generic"),
    (lambda d: d["experiment"].update(channel=["HN", "Reddit"]), "one channel"),
    (lambda d: d["experiment"].pop("not_this_round"), "not this round"),
    (lambda d: d["experiment"]["success"].pop("failure"), "missing failure"),
    (lambda d: d["pains"][0].update(fit="very high"), "fit must be"),
    (lambda d: d.update(pmf_score=78), "no scores or percentages"),
    (lambda d: d["pains"][0]["source_ids"].append("nope"), "unknown source nope"),
])
def test_rules_reject(repo, mutate, needle):
    d = copy.deepcopy(EX)
    mutate(d)
    assert any(needle in e for e in errs(d, repo)), errs(d, repo)


def test_gate_stop_forbids_an_experiment(repo):
    d = copy.deepcopy(EX)
    d["gate"], d["gate_missing"] = "stop", ["no proof"]
    assert any("no experiment until" in e for e in errs(d, repo))
    d.pop("experiment")
    assert errs(d, repo) == []


# ── renderer ────────────────────────────────────────────────────────────
def test_render_marks_paraphrases_and_escapes():
    d = copy.deepcopy(EX)
    d["sources"][0]["verbatim"] = False
    d["pains"][0]["statement"] = "<script>x</script>"
    html = render.render(d, [])
    assert "(paraphrase)" in html and "&lt;script&gt;" in html and "<script>" not in html
    assert "Where is the pull for typedmem?" in html and "The one next experiment" in html


def test_render_gate_stop():
    d = copy.deepcopy(EX)
    d["gate"], d["gate_missing"] = "stop", ["No proof yet"]
    d.pop("experiment")
    html = render.render(d, [])
    assert "Not ready for go-to-market" in html and "No proof yet" in html


# ── value mode ──────────────────────────────────────────────────────────
EXV = json.loads((Path(__file__).parent / "example_value.json").read_text())


def value_fixture():
    """The TypedMem value map, re-pointed at the throwaway repo's files."""
    v = copy.deepcopy(EXV)
    def fix(ev):
        if ev.get("file"):
            ev.update(file="README.md", line=5)
    for c in v["capabilities"]:
        for ev in c["evidence"]:
            fix(ev)
    for x in v["values"]:
        for ev in x.get("proof") or []:
            fix(ev)
    for ev in v["problem"]["evidence"]:
        fix(ev)
    for s in v["first_screen"]["stop_saying"]:
        fix(s)
    return v


def test_example_value_valid(repo):
    assert validate.validate_value(value_fixture(), repo, EX) == []


def _val(v, vid):
    return next(x for x in v["values"] if x["id"] == vid)


@pytest.mark.parametrize("mutate,needle", [
    (lambda v: _val(v, "V1").update(proof=[]), "demonstrated needs a confirmed proof"),
    (lambda v: _val(v, "V4").update(proof=[{"level": "confirmed", "kind": "test", "claim": "x", "file": "README.md", "line": 1}]), "call it demonstrated"),
    (lambda v: _val(v, "V1").update(level="certain"), "level must be one of"),
    (lambda v: _val(v, "V1").update(capabilities=["nope"]), "unknown capability nope"),
    (lambda v: _val(v, "V1").update(pains=["P9"]), "unknown pain P9"),
    (lambda v: v["first_screen"].update(lead=["V7"]), "is a hypothesis"),
    (lambda v: v["first_screen"].update(lead=["V1", "V2"]), "exactly one value"),
    (lambda v: v["first_screen"]["stop_saying"][0].pop("file"), "where the claim is made"),
    (lambda v: v["capabilities"][0].update(evidence=[]), "needs a code or doc locator"),
    (lambda v: v.update(value_score=9), "no scores"),
])
def test_value_rules_reject(repo, mutate, needle):
    v = value_fixture()
    mutate(v)
    errs = validate.validate_value(v, repo, EX)
    assert any(needle in e for e in errs), errs


def test_coverage_is_derived_and_finds_orphans():
    cov = validate.coverage(EXV)
    assert cov["recall"] == [] and cov["http"] == [] and "V1" in cov["state"]


def test_render_value_map_bridge_and_first_screen():
    html = render.render(copy.deepcopy(EX), [], copy.deepcopy(EXV))
    assert html.index("What value does typedmem create?") < html.index("Where is the pull for typedmem?")
    assert "Inside ↔ outside" in html and "no mapped value answers this" in html      # P3 is unanswered
    assert "no mapped value" in html and "Stop saying" in html
    only = render.render(None, [], copy.deepcopy(EXV))
    assert "What value does typedmem create?" in only and "Where is the pull" not in only


# ── report v2: five scenes, evidence on demand ──────────────────────────
import re as _re


def _default_view(html):
    """Everything a reader sees before opening the evidence or a panel."""
    main = html[:html.index('<details class="evidence">')]
    return _re.sub(r"<template.*?</template>", "", main, flags=_re.S)


def test_v2_has_five_scenes_in_order_and_evidence_behind_a_click():
    html = render.render(copy.deepcopy(EX), [], copy.deepcopy(EXV))
    acts = [m for m in _re.findall(r'<div class="act">(\d) · (\w+)</div>', _default_view(html))]
    assert acts == [("1", "Value"), ("2", "Pull"), ("3", "Coverage"), ("4", "Story"), ("5", "Move")]
    ev = html[html.index('<details class="evidence">'):]
    assert "Where is the pull for typedmem?" in ev and "In their words" not in _default_view(html)


def test_v2_default_view_has_no_long_paragraphs():
    """Design rule: no paragraph longer than about two lines in the default view."""
    for doc, val in ((EX, EXV), (None, EXV)):
        view = _default_view(render.render(copy.deepcopy(doc) if doc else None, [], copy.deepcopy(val)))
        for p in _re.findall(r"<p(?:\s[^>]*)?>(.*?)</p>", view, flags=_re.S):
            text = _re.sub(r"<[^>]+>", "", p)
            assert len(text) <= 180, text


def test_v2_encodes_conclusions_visually():
    view = _default_view(render.render(copy.deepcopy(EX), [], copy.deepcopy(EXV)))
    assert 'data-d="V1"' in view and 'data-d="P1"' in view            # clickable nodes
    assert "no mapped value" in view and "NO MAPPED VALUE" in view    # unanswered pain, orphan capability
    assert "STOP SAYING" in view and '<div class="mv goal">' in view  # story and move
    assert view.count('stroke-width="') > 5                           # bridge line widths


def test_v2_every_value_and_pain_has_a_detail_panel():
    html = render.render(copy.deepcopy(EX), [], copy.deepcopy(EXV))
    for x in EXV["values"]:
        assert f'<template id="d-{x["id"]}">' in html
    for p in EX["pains"]:
        assert f'<template id="d-{p["id"]}">' in html


def test_v2_without_market_evidence_says_so_in_one_line():
    view = _default_view(render.render(None, [], copy.deepcopy(EXV)))
    assert "No market evidence yet" in view and "No experiment yet" in view
