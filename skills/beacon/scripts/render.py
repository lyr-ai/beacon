"""Render .beacon/launch.json as a self-contained report (Beacon, phase 6).

    python3 render.py .beacon/launch.json [--history .beacon/history] -o .beacon/report.html

One HTML file, no server. The report is ordered as a decision: is the
positioning ready (the gate), where the pull is (the pains, one dot per
independent author), who has the problem (the audiences), and then the one
next experiment. Verbatim quotes are shown as quotes; paraphrases are
labelled as paraphrases.
"""

from __future__ import annotations

import html
import json
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from pathlib import Path

e = lambda s: html.escape(str(s if s is not None else ""))
PLAT = {"hn": "Hacker News", "github": "GitHub", "reddit": "Reddit", "web": "Web"}

CSS = """
:root{--paper:#f5f0e6;--ink:#2a2826;--muted:#7a7368;--rule:#d8cfbf;--wash:#ede5d6;--sage:#4f6f58;
--cinnabar:#b8432c;--ochre:#9c7424;--serif:Newsreader,Georgia,"Times New Roman",serif;
--mono:"IBM Plex Mono",ui-monospace,Menlo,monospace;--sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--paper:#1a1916;--ink:#ebe5d9;--muted:#9c9587;
--rule:#3b3731;--wash:#24221e;--sage:#93b69d;--cinnabar:#e2765c;--ochre:#d0a95b}}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans)}
main{max-width:920px;margin:0 auto;padding:36px 16px 72px}
.fig{font:500 11px var(--mono);letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
h1{font:600 38px/1.1 var(--serif);margin:8px 0 8px;letter-spacing:-.01em}
.lede{font:400 18px/1.5 var(--serif);color:var(--muted);margin:0 0 20px;max-width:62ch}
h2{font:400 26px/1.2 var(--serif);margin:40px 0 12px;border-top:1px solid var(--rule);padding-top:22px}
h4{font:500 11px var(--mono);letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin:0 0 6px}
.gate{font:600 11px var(--mono);letter-spacing:.12em;text-transform:uppercase;padding:2px 8px;border-radius:3px}
.gate.pass{background:var(--sage);color:var(--paper)}.gate.stop{background:var(--cinnabar);color:var(--paper)}
.pos{display:grid;grid-template-columns:110px minmax(0,1fr);gap:8px 16px}
.pos .k{font:500 11px/1.9 var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.pos .v{font:400 16px/1.5 var(--serif)}.pos .v small{display:block;font:400 12px var(--mono);color:var(--muted)}
.pos a,.q a,.src a{color:inherit}
.pain{border-top:1px solid var(--rule);padding:16px 0}
.pain .st{font:400 21px/1.3 var(--serif);margin:0 0 8px}
.dots{display:flex;gap:5px;flex-wrap:wrap;align-items:center;margin:0 0 6px}
.dot{width:13px;height:13px;border-radius:50%;display:inline-block}
.dot.hn{background:var(--ochre)}.dot.github{background:var(--ink)}.dot.reddit{background:var(--sage)}.dot.web{border:1.5px solid var(--muted)}
.dots .n{font:500 12px var(--mono);color:var(--muted);margin-left:8px}
.fit{font:600 10.5px var(--mono);letter-spacing:.12em;text-transform:uppercase}
.fit.high,.fit.strong{color:var(--sage)}.fit.partial{color:var(--ochre)}.fit.none,.fit.weak{color:var(--muted)}
.lang{font:italic 400 16px/1.5 var(--serif);color:var(--ink);margin:6px 0}
.q{font:400 14.5px/1.55 var(--sans);margin:8px 0;padding-left:12px;border-left:2px solid var(--rule)}
.q.para{font-style:italic;color:var(--muted)}
.q .who{display:block;font:400 11.5px var(--mono);color:var(--muted);margin-top:2px}
details summary{cursor:pointer;font:500 13px var(--sans);margin-top:6px}
.aud{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}
.aud div{border-top:2px solid var(--ink);padding-top:8px;font:400 14.5px/1.5 var(--sans)}
.aud b{font:400 18px/1.3 var(--serif);display:block;margin:4px 0}
.exp{background:var(--wash);padding:22px 22px 18px;border-radius:4px;margin-top:12px}
.formula{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px 18px;font:400 17px/1.35 var(--serif);margin:6px 0 16px}
@media (max-width:720px){.formula{grid-template-columns:1fr 1fr}}
.formula span b{display:block;font:500 10.5px var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
pre.msg{white-space:pre-wrap;font:400 14.5px/1.6 var(--sans);background:var(--paper);padding:14px;border-radius:3px;margin:8px 0 14px}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:18px}
ul{margin:0;padding-left:18px;font:400 14.5px/1.55 var(--sans)}
.legend{font:400 12px var(--mono);color:var(--muted);display:flex;gap:16px;flex-wrap:wrap;margin:8px 0 0}
.vproblem{font:400 22px/1.35 var(--serif);text-align:center;margin:8px auto 0;max-width:36ch}
.vstem{width:1px;height:22px;background:var(--rule);margin:0 auto}
.vrow{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:16px;border-top:1px solid var(--rule);padding-top:14px}
.vcard{padding:10px 0}.vcard .role{font:600 10.5px var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.vcard .role.lead{color:var(--sage)}
.vcard .o{font:400 19px/1.3 var(--serif);margin:4px 0}.vcard .y{font:400 14px/1.5 var(--sans);color:var(--muted)}
.lv{font:600 10.5px var(--mono);letter-spacing:.1em;text-transform:uppercase}
.lv.demonstrated{color:var(--sage)}.lv.supported{color:var(--ochre)}.lv.hypothesis{color:var(--muted)}
.vcard.hypothesis .o{font-style:italic;color:var(--muted)}
.cov{border-collapse:collapse;font:400 13px var(--sans);width:100%;margin:6px 0}
.cov th{font:500 10.5px var(--mono);letter-spacing:.06em;color:var(--muted);padding:5px 6px;text-align:center}
.cov th.c{text-align:left;font:400 14px var(--serif);color:var(--ink)}
.cov td{text-align:center;border-top:1px solid var(--rule);padding:5px 6px;font:600 14px var(--mono)}
.cov tr.orphan th.c{color:var(--cinnabar)}
.fs{display:grid;grid-template-columns:120px minmax(0,1fr);gap:8px 16px;font:400 15px/1.5 var(--sans)}
.fs .k{font:500 11px/1.9 var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.fs .k.lead{color:var(--sage)}.fs .k.stop{color:var(--cinnabar)}.fs a,.vcard a{color:inherit}
.foot{font:400 12.5px/1.6 var(--mono);color:var(--muted);margin-top:40px;border-top:1px solid var(--rule);padding-top:14px}
@media (max-width:620px){h1{font-size:30px}.pos{grid-template-columns:1fr}.cols{grid-template-columns:1fr}}
"""


def loc(ev: dict, web: str | None) -> str:
    if ev.get("url"):
        return f'<a href="{e(ev["url"])}">{e(ev["url"])}</a>'
    f = e(ev.get("file")) + (f":{ev['line']}" if ev.get("line") else "")
    if web and ev.get("file"):
        return f'<a href="{e(web)}/blob/HEAD/{e(ev["file"])}#L{e(ev.get("line", 1))}">{f}</a>'
    return f


def quote(s: dict) -> str:
    who = f'{e(s.get("author"))} · {PLAT.get(s.get("platform"), s.get("platform"))} · {e(s.get("date"))}'
    cls = "q" if s.get("verbatim") else "q para"
    txt = f"“{e(s.get('quote'))}”" if s.get("verbatim") else f"{e(s.get('quote'))} (paraphrase)"
    return f'<div class="{cls}">{txt}<span class="who">{who} · <a href="{e(s.get("url"))}">source</a></span></div>'


LEVEL_GLYPH = {"demonstrated": "●", "supported": "◐", "hypothesis": "○"}


def _authors(pain: dict, by_id: dict) -> int:
    return len({(by_id[s]["platform"], by_id[s]["author"].lower()) for s in pain.get("source_ids", []) if s in by_id})


def value_section(v: dict, launch: dict | None) -> str:
    web = f"https://github.com/{v['product']['repo']}" if v.get("product", {}).get("repo") else None
    caps = {c["id"]: c for c in v.get("capabilities") or []}
    vals = v.get("values") or []
    fs = v.get("first_screen") or {}
    role = {}
    for part in ("lead", "support", "trust"):
        for vid in fs.get(part) or []:
            role[vid] = part
    order = sorted(vals, key=lambda x: (["lead", "support", "trust"].index(role[x["id"]]) if x["id"] in role else 3,
                                        list(LEVEL_GLYPH).index(x.get("level", "hypothesis"))))
    by_id = {s["id"]: s for s in (launch or {}).get("sources") or []}
    pains = {p["id"]: p for p in (launch or {}).get("pains") or []}
    out = [f'<p class="vproblem">{e((v.get("problem") or {}).get("text"))}</p><div class="vstem"></div><div class="vrow">']
    for x in order:
        chips = " ".join(f'<span class="fig" style="border:1px solid var(--rule);padding:0 5px;border-radius:3px">{e(caps.get(c, {}).get("name", c))}</span>'
                         for c in x.get("capabilities") or [])
        proof = "".join(f'<li>{e(p.get("claim"))}{loc(p, web) if (p.get("file") or p.get("url")) else ""}'
                        + (f'<span class="loc" style="display:block;font:400 11.5px var(--mono);color:var(--muted)">$ {e(p.get("command"))} → {e(p.get("output"))}</span>' if p.get("command") else "")
                        + "</li>" for p in x.get("proof") or [])
        pl = ", ".join(f"{pid} ({_authors(pains[pid], by_id)} people)" for pid in x.get("pains") or [] if pid in pains)
        out.append(f"""<div class="vcard {e(x.get('level'))}"><div class="role {e(role.get(x['id'], ''))}">{e(role.get(x['id'], 'value'))} · {e(x['id'])}</div>
<div class="o">{e(x.get('outcome'))}</div><div class="y">{e(x.get('why'))}</div>
<div style="margin-top:6px"><span class="lv {e(x.get('level'))}">{LEVEL_GLYPH.get(x.get('level'), '?')} {e(x.get('level'))}</span></div>
<details><summary>How and proof</summary><div style="margin:6px 0">{chips}</div>{f'<ul>{proof}</ul>' if proof else '<p class="y">No outside measurement.</p>'}
{f'<p class="y">Answers: {e(pl)}</p>' if pl else '<p class="y">Answers no observed pain.</p>'}</details></div>""")
    out.append("</div>")
    out.append('<div class="legend"><span>● demonstrated: test, benchmark or command proof</span><span>◐ supported: code, no outside measurement</span><span>○ hypothesis: a guess worth testing</span></div>')

    # inside ↔ outside bridge
    if launch:
        pl = sorted(pains.values(), key=lambda p: -_authors(p, by_id))
        left = order
        rowh, W = 46, 860
        H = max(len(left), len(pl)) * rowh + 40
        lx, rx = 300, W - 300
        ly = {x["id"]: 42 + i * rowh for i, x in enumerate(left)}
        ry = {p["id"]: 42 + i * rowh for i, p in enumerate(pl)}
        svg = [f'<svg viewBox="0 0 {W} {H}" style="width:100%;height:auto;display:block;margin-top:8px" role="img" aria-label="Values linked to observed pains">']
        linked_p = set()
        for x in left:
            for pid in x.get("pains") or []:
                if pid in ry:
                    linked_p.add(pid)
                    y1, y2 = ly[x["id"]], ry[pid]
                    svg.append(f'<path d="M{lx + 8},{y1} C{lx + 110},{y1} {rx - 110},{y2} {rx - 8},{y2}" fill="none" stroke="var(--sage)" stroke-width="1.8" opacity=".8"/>')
        for x in left:
            y = ly[x["id"]]
            fill = "var(--ink)" if x.get("pains") else "var(--muted)"
            txt = (x.get("outcome") or "")[:40] + ("…" if len(x.get("outcome") or "") > 40 else "")
            svg.append(f'<text x="{lx - 8}" y="{y + 4}" text-anchor="end" font-family="Newsreader,Georgia,serif" font-size="15" fill="{fill}">{e(txt)}</text>')
            cx, lvl = lx + 4, x.get("level")
            if lvl == "demonstrated":      # ● filled
                svg.append(f'<circle cx="{cx}" cy="{y}" r="5" fill="{fill}"/>')
            elif lvl == "supported":       # ◐ half-filled
                svg.append(f'<circle cx="{cx}" cy="{y}" r="5" fill="var(--paper)" stroke="{fill}" stroke-width="1.5"/>'
                           f'<path d="M{cx},{y - 5} A5,5 0 0,0 {cx},{y + 5} Z" fill="{fill}"/>')
            else:                          # ○ hollow
                svg.append(f'<circle cx="{cx}" cy="{y}" r="5" fill="var(--paper)" stroke="{fill}" stroke-width="1.5"/>')
            if not x.get("pains"):
                svg.append(f'<text x="{lx + 16}" y="{y + 4}" font-family="IBM Plex Mono,monospace" font-size="11" fill="var(--muted)">? no observed pain</text>')
        for p in pl:
            y = ry[p["id"]]
            n = _authors(p, by_id)
            txt = (p.get("statement") or "")[:44] + ("…" if len(p.get("statement") or "") > 44 else "")
            col = "var(--ink)" if p["id"] in linked_p else "var(--cinnabar)"
            svg.append(f'<circle cx="{rx - 4}" cy="{y}" r="4.5" fill="{col}"/>')
            svg.append(f'<text x="{rx + 6}" y="{y + 4}" font-family="Newsreader,Georgia,serif" font-size="15" fill="{col}">{e(txt)}</text>')
            svg.append(f'<text x="{rx + 6}" y="{y + 18}" font-family="IBM Plex Mono,monospace" font-size="10.5" fill="var(--muted)">{e(p["id"])} · {n} people{"" if p["id"] in linked_p else " · no mapped value answers this"}</text>')
        svg.append(f'<text x="{lx - 6}" y="12" text-anchor="end" font-family="IBM Plex Mono,monospace" font-size="10.5" letter-spacing="1.5" fill="var(--muted)">WHAT WE PROVIDE</text>')
        svg.append(f'<text x="{rx + 6}" y="12" font-family="IBM Plex Mono,monospace" font-size="10.5" letter-spacing="1.5" fill="var(--muted)">WHAT PEOPLE ASK FOR</text>')
        svg.append("</svg>")
        out.append("<h2>Inside ↔ outside: which values meet observed pain</h2>" + "".join(svg)
                   + '<div class="legend"><span>node: ● demonstrated · ◐ supported · ○ hypothesis</span><span>a line = the value answers that pain</span>'
                   '<span style="color:var(--cinnabar)">red = a pain no mapped value answers</span></div>')

    # coverage
    cov = {c: [] for c in caps}
    for x in vals:
        for c in x.get("capabilities") or []:
            cov.setdefault(c, []).append(x["id"])
    head = "".join(f'<th title="{e(x.get("outcome"))}">{e(x["id"])}</th>' for x in order)
    orphan_tag = ' <span class="fig" style="color:var(--cinnabar)">no mapped value</span>'
    rows = ""
    for cid, c in caps.items():
        used = cov.get(cid, [])
        cells = "".join("<td>" + ("●" if x["id"] in used else "") + "</td>" for x in order)
        rows += ('<tr class="' + ("" if used else "orphan") + '"><th class="c">' + e(c.get("name"))
                 + ("" if used else orphan_tag) + "</th>" + cells + "</tr>")
    out.append(f'<h2>Feature → value coverage</h2><table class="cov"><tr><th></th>{head}</tr>{rows}</table>')

    # first screen
    if fs:
        vname = {x["id"]: x.get("outcome") for x in vals}
        rowsfs = []
        for part, label in (("lead", "Lead with"), ("support", "Support"), ("trust", "Trust")):
            if fs.get(part):
                rowsfs.append(f'<div class="k {part}">{label}</div><div>{"<br>".join(e(vname.get(i, i)) for i in fs[part])}</div>')
        if fs.get("advanced"):
            rowsfs.append('<div class="k">Advanced, don\'t lead</div><div>' + "<br>".join(
                f'{e(caps.get(a["capability"], {}).get("name", a["capability"]))} <span style="color:var(--muted)">— {e(a.get("reason"))}</span>' for a in fs["advanced"]) + "</div>")
        if fs.get("stop_saying"):
            rowsfs.append('<div class="k stop">Stop saying</div><div>' + "<br>".join(
                f'“{e(x.get("claim"))}” <span style="color:var(--muted)">{loc(x, web)} — {e(x.get("reason"))}</span>' for x in fs["stop_saying"]) + "</div>")
        out.append('<h2>Recommended first screen</h2><div class="fs">' + "".join(rowsfs) + "</div>")
    return "\n".join(out)


def _render_v1(doc: dict | None, history: list[dict], value: dict | None = None) -> str:
    if doc is None:
        doc = {"product": (value or {}).get("product", {}), "gate": None, "sources": [], "pains": []}
    prod = doc.get("product", {})
    name = prod.get("name", "this project")
    web = f"https://github.com/{prod['repo']}" if prod.get("repo") else None
    by_id = {s["id"]: s for s in doc.get("sources") or []}
    gate = doc.get("gate")
    out = [f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Beacon · {e(name)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,600;1,6..72,400&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body><main>
<div class="fig">Beacon · {e(name)} · {e(prod.get('date', ''))}</div>
<h1>{"What value does " + e(name) + " create?" if value else "Where is the pull for " + e(name) + "?"}</h1>"""]
    if value:
        vals = value.get("values") or []
        tally = ", ".join(f"{sum(x.get('level') == l for x in vals)} {l}" for l in LEVEL_GLYPH)
        out.append(f'<p class="lede">{len(vals)} values ({tally}), each traced from a capability to a user outcome and its proof.</p>')
        out.append(value_section(value, doc if doc.get("pains") else None))
        if doc.get("gate") is None:
            out.append("<p class=\"foot\">Generated by Beacon (value).</p></main></body></html>")
            return "\n".join(out)
        out.append(f'<h2 style="font-size:32px;border-top:2px solid var(--ink)">Where is the pull for {e(name)}?</h2>')
    pains = doc.get("pains") or []
    authors = {(by_id[s]["platform"], by_id[s]["author"].lower()) for p in pains for s in p.get("source_ids", []) if s in by_id}
    verb = sum(1 for s in by_id.values() if s.get("verbatim"))
    out.append(f'<p class="lede">Positioning gate <span class="gate {e(gate)}">{e(gate)}</span>. '
               + (f"{len(pains)} pains from {len(authors)} independent people in {len(by_id)} sources "
                  f"({verb} quoted verbatim). One next experiment below.</p>" if gate == "pass" else
                  "Not ready for go-to-market yet: the positioning can't be stated with evidence.</p>"))

    pos = doc.get("positioning") or {}
    out.append("<h2>What it sells</h2><div class='pos'>")
    for f in ("problem", "failure", "product", "proof", "boundary"):
        item = pos.get(f) or {}
        ev = " · ".join(loc(x, web) for x in item.get("evidence") or [])
        out.append(f'<div class="k">{f}</div><div class="v">{e(item.get("text") or "— missing —")}<small>{ev}</small></div>')
    out.append("</div>")
    if gate == "stop":
        out.append("<h2>Missing before go-to-market</h2><ul>" + "".join(f"<li>{e(m)}</li>" for m in doc.get("gate_missing") or []) + "</ul>")

    if pains:
        out.append("<h2>The pull: pains, in people's words</h2>")
        if doc.get("coverage_notes"):
            out.append(f'<p style="font:italic 400 15px/1.5 var(--serif);color:var(--muted);margin:0 0 8px;max-width:68ch">Coverage: {e(doc["coverage_notes"])}</p>')
        out.append('<div class="legend"><span><span class="dot hn"></span> Hacker News</span><span><span class="dot github"></span> GitHub</span>'
                   '<span><span class="dot reddit"></span> Reddit</span><span><span class="dot web"></span> Web</span>'
                   '<span>one dot per independent person</span></div>')
        for p in sorted(pains, key=lambda p: -len({(by_id[s]["platform"], by_id[s]["author"].lower()) for s in p.get("source_ids", []) if s in by_id})):
            people = {}
            for s in p.get("source_ids", []):
                if s in by_id:
                    people.setdefault((by_id[s]["platform"], by_id[s]["author"].lower()), by_id[s])
            dots = "".join(f'<span class="dot {e(k[0])}" title="{e(v["author"])}"></span>' for k, v in people.items())
            lang = " · ".join(f"“{e(x['text'])}”" for x in p.get("language") or [])
            wk = "".join(f"<li>{e(w.get('text'))}</li>" for w in p.get("workarounds") or [])
            quotes = "".join(quote(by_id[s]) for s in p.get("source_ids", []) if s in by_id)
            out.append(f"""<section class="pain"><div class="fig">{e(p.get('id'))} · fit <span class="fit {e(p.get('fit'))}">{e(p.get('fit'))}</span></div>
<p class="st">{e(p.get('statement'))}</p>
<div class="dots">{dots}<span class="n">{len(people)} independent {'person' if len(people) == 1 else 'people'}</span></div>
{f'<p class="lang">{lang}</p>' if lang else ''}
<p style="font:400 14px/1.5 var(--sans);color:var(--muted);margin:4px 0">Fit: {e(p.get('fit_reason'))}</p>
<details><summary>Sources and workarounds</summary>{f'<h4 style="margin-top:10px">What people do today</h4><ul>{wk}</ul>' if wk else ''}{quotes}</details></section>""")
    ce = doc.get("counter_evidence") or []
    if ce:
        out.append("<h2>Against</h2><ul>" + "".join(
            f"<li>{e(c.get('claim'))} " + " ".join(f'<a href="{e(by_id[s]["url"])}">[{e(by_id[s]["author"])}]</a>'
                                                   for s in c.get("source_ids", []) if s in by_id) + "</li>" for c in ce) + "</ul>")

    auds = doc.get("audiences") or []
    if auds:
        out.append("<h2>Who has it</h2><div class='aud'>" + "".join(
            f"<div><span class='fit {e(a.get('fit'))}'>{e(a.get('fit'))} fit</span><b>{e(a.get('who'))}</b>"
            f"Building: {e(a.get('building'))}<br>Cares when: {e(a.get('trigger'))}<br>"
            f"<span style='color:var(--muted)'>Talks in: {e(', '.join(a.get('where') or []))}</span></div>" for a in auds) + "</div>")

    ex = doc.get("experiment")
    if ex:
        aud = next((a for a in auds if a.get("id") == ex.get("audience")), {})
        sc = ex.get("success") or {}
        why = "".join(f"<li>{e(w.get('reason'))}</li>" for w in ex.get("why_channel") or [])
        nt = "".join(f"<li><b>{e(n.get('item'))}</b>: {e(n.get('reason'))}</li>" for n in ex.get("not_this_round") or [])
        out.append(f"""<h2>The one next experiment</h2><div class="exp">
<div class="formula"><span><b>audience</b>{e(aud.get('who', ex.get('audience')))}</span><span><b>hook</b>{e(ex.get('hook'))}</span><span><b>channel</b>{e(ex.get('channel'))}</span><span><b>ask</b>{e(ex.get('cta'))}</span></div>
<h4>Hypothesis</h4><p style="font:400 16px/1.5 var(--serif);margin:0 0 12px">{e(ex.get('hypothesis'))}</p>
<h4>Draft</h4><pre class="msg">{e(ex.get('message'))}</pre>
<div class="cols"><div><h4>Success</h4><ul><li>{e(sc.get('signal'))}: <b>{e(sc.get('threshold'))}</b> within {e(sc.get('window_hours'))}h</li>
<li>Failure: {e(sc.get('failure'))}</li></ul></div><div><h4>Why this channel</h4><ul>{why}</ul></div></div>
<h4 style="margin-top:14px">Not this round</h4><ul>{nt}</ul>
<p class="fig" style="margin-top:14px">Record results with <b>/beacon record</b> → {e(ex.get('history_file'))}</p></div>""")

    if history:
        rows = "".join(f"<li>{e(h.get('date', ''))} · {e((h.get('experiment') or {}).get('channel'))} · "
                       f"{e(h.get('decision') or 'results pending')}</li>" for h in history)
        out.append(f"<h2>Past experiments</h2><ul>{rows}</ul>")
    qs = doc.get("queries") or []
    out.append(f'<p class="foot">Searched: {e("; ".join(q.get("query", "") for q in qs))}<br>'
               "Generated by Beacon. Quotes marked “…” are people's own words; paraphrases are labelled.</p>")
    out.append("</main></body></html>")
    return "\n".join(out)


def render(doc: dict | None, history: list[dict], value: dict | None = None) -> str:
    """v2 (five visual scenes, evidence on demand) when a value map exists;
    otherwise the v1 research page. v2 keeps the whole v1 page, unchanged,
    behind "See the evidence"."""
    v1 = _render_v1(doc, history, value)
    if not value:
        return v1
    from scenes import render_v2
    inner = v1[v1.index("<main>") + len("<main>"):v1.rindex("</main>")]
    launch = doc if doc and doc.get("pains") else None
    return render_v2(value, launch, inner, loc, CSS)


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: render.py .beacon/launch.json | --value .beacon/value.json [--history DIR] -o report.html")
        return 2
    if "--value" in argv:
        vpath = Path(argv[argv.index("--value") + 1]); base = vpath.parent
        lp = base / "launch.json"
        doc = json.loads(lp.read_text()) if lp.exists() else None
    else:
        base = Path(argv[0]).parent
        doc = json.loads(Path(argv[0]).read_text())
        vpath = base / "value.json"
    value = json.loads(vpath.read_text()) if vpath.exists() else None
    hdir = Path(argv[argv.index("--history") + 1]) if "--history" in argv else base / "history"
    hist = [json.loads(p.read_text()) for p in sorted(hdir.glob("*.json"))] if hdir.exists() else []
    outp = Path(argv[argv.index("-o") + 1]) if "-o" in argv else Path("report.html")
    outp.write_text(render(doc, hist, value))
    print(f"wrote {outp}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
