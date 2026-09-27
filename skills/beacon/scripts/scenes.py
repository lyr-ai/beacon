"""Beacon report v2: five visual scenes, evidence on demand.

    VALUE → PULL → COVERAGE → STORY → MOVE

Design rules (checked by tests):
- the default view never makes the reader read research before seeing the
  conclusion: no paragraph in it is longer than about two lines;
- every major conclusion has a visual encoding. Node size is the role
  (lead / support / trust / other); node fill is the evidence level
  (● demonstrated, ◐ supported, ○ hypothesis); line width is independent
  voices; red is a pain no mapped value answers;
- clicking any node opens its evidence in a side panel. The full research
  (quotes, sources, audiences, experiment rationale) sits behind
  "See the evidence", unchanged.

Everything is pre-rendered into the HTML: the only script opens and closes the
panel, so the page works offline.
"""

from __future__ import annotations

import html
import math

e = lambda s: html.escape(str(s if s is not None else ""))
ROLES = ("lead", "support", "trust")


GLYPH = {"demonstrated": "●", "supported": "◐", "hypothesis": "○"}


def short(text: str | None, words: int = 6, chars: int | None = None) -> str:
    ws = (text or "").split()
    while chars and len(ws[:words]) > 1 and len(" ".join(ws[:words])) > chars:
        words -= 1
    return " ".join(ws[:words]) + ("…" if len(ws) > words else "")


def authors(pain: dict, by_id: dict) -> int:
    return len({(by_id[s]["platform"], by_id[s]["author"].lower()) for s in pain.get("source_ids", []) if s in by_id})


def wrap(text: str | None, width: int, lines: int = 2) -> list[str]:
    """Break text into at most ``lines`` lines of about ``width`` characters;
    the last line ends in … if anything was cut."""
    out, cur = [], ""
    words = (text or "").split()
    for i, w in enumerate(words):
        if len(cur) + len(w) + (1 if cur else 0) <= width:
            cur = f"{cur} {w}".strip()
        else:
            out.append(cur)
            cur = w
            if len(out) == lines:
                out[-1] = out[-1].rstrip(",.;:") + "…"
                return out
    out.append(cur)
    return out[:lines]


def tspans(x, lines: list[str], lh: int) -> str:
    return "".join(f'<tspan x="{x}" dy="{0 if i == 0 else lh}">{e(t)}</tspan>' for i, t in enumerate(lines))


def node(cx, cy, r, level, color="var(--ink)") -> str:
    """Evidence level as fill: ● filled, ◐ half, ○ hollow."""
    if level == "demonstrated":
        return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}"/>'
    if level == "supported":
        return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="var(--paper)" stroke="{color}" stroke-width="2"/>'
                f'<path d="M{cx},{cy - r} A{r},{r} 0 0,0 {cx},{cy + r} Z" fill="{color}"/>')
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="var(--paper)" stroke="{color}" stroke-width="2"/>'


CSS = """
.scene{padding:34px 0 30px;border-top:1px solid var(--rule)}
.scene:first-of-type{border-top:0}
.act{font:500 11px var(--mono);letter-spacing:.18em;text-transform:uppercase;color:var(--muted)}
.scene h2{border:0;padding:0;margin:4px 0 4px;font:400 30px/1.2 var(--serif)}
.say{font:400 17px/1.5 var(--serif);color:var(--muted);margin:0 0 14px;max-width:60ch}
.scene svg{width:100%;height:auto;display:block;overflow:visible}
.hit{cursor:pointer}.hit:hover .lbl{text-decoration:underline}
.key{font:400 12px var(--mono);color:var(--muted);display:flex;gap:18px;flex-wrap:wrap;margin-top:6px}
#panel{position:fixed;top:0;right:0;height:100%;width:min(440px,100%);background:var(--paper);border-left:1px solid var(--rule);
 box-shadow:-8px 0 30px rgba(0,0,0,.08);padding:26px 24px;overflow-y:auto;transform:translateX(105%);transition:transform .25s;z-index:5}
#panel.on{transform:none}#panel .x{float:right;background:none;border:0;font:400 22px var(--sans);cursor:pointer;color:var(--muted)}
#panel h3{font:400 22px/1.3 var(--serif);margin:6px 0 8px}#panel p,#panel li{font:400 14.5px/1.55 var(--sans)}
#panel ul{padding-left:18px}#panel a{color:inherit}
.evidence{margin-top:30px;border-top:2px solid var(--ink);padding-top:10px}
.evidence>summary{font:600 15px var(--sans);cursor:pointer;padding:8px 0}
.funnel{display:flex;flex-direction:column;align-items:center;gap:6px}
.fn{border:1.5px solid var(--ink);border-radius:4px;padding:10px 18px;text-align:center;font:400 17px/1.35 var(--serif);cursor:pointer}
.because{font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.5px;color:var(--muted);margin:-2px 0 2px}.because b{color:var(--sage);font-weight:500}
.fn.lead{border:2.5px solid var(--sage);font-size:23px;padding:14px 26px;max-width:620px}
.fn.support,.fn.trust{max-width:520px}.fn.adv{border-style:dashed;color:var(--muted);font-size:14px;max-width:480px}
.fn .r{display:block;font:600 10.5px var(--mono);letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin-bottom:3px}
.fn.lead .r{color:var(--sage)}
.arrow{color:var(--muted);font:400 18px var(--sans)}
.storyrow{display:grid;grid-template-columns:minmax(0,1fr) 230px;gap:22px;align-items:center}
.stop{border:1.5px solid var(--cinnabar);border-radius:4px;padding:12px 14px;color:var(--cinnabar)}
.stop .r{font:600 10.5px var(--mono);letter-spacing:.14em}.stop div{font:400 14.5px/1.4 var(--serif);margin-top:6px;color:var(--ink)}
.stop div s{color:var(--muted)}
.move{display:flex;flex-direction:column;align-items:center;gap:4px}
.mv{font:400 18px/1.35 var(--serif);text-align:center;max-width:560px}
.mv .r{display:block;font:600 10.5px var(--mono);letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
.mv.goal{border:2px solid var(--sage);border-radius:4px;padding:10px 18px}
@media (max-width:680px){.storyrow{grid-template-columns:1fr}.scene h2{font-size:24px}}
"""

JS = """
const P=document.getElementById('panel');
function openP(id){const t=document.getElementById('d-'+id);if(!t)return;P.querySelector('.body').innerHTML=t.innerHTML;P.classList.add('on');}
document.addEventListener('click',ev=>{const h=ev.target.closest('[data-d]');if(h){openP(h.dataset.d);return;}
 if(ev.target.closest('.x')||(!ev.target.closest('#panel')&&P.classList.contains('on')))P.classList.remove('on');});
document.addEventListener('keydown',ev=>{if(ev.key==='Escape')P.classList.remove('on');});
"""


def ordered_values(v: dict) -> tuple[list[dict], dict]:
    fs = v.get("first_screen") or {}
    role = {vid: part for part in ROLES for vid in fs.get(part) or []}
    lvl = ("demonstrated", "supported", "hypothesis")
    vals = sorted(v.get("values") or [], key=lambda x: (ROLES.index(role[x["id"]]) if x["id"] in role else 3,
                                                          lvl.index(x.get("level", "hypothesis"))))
    return vals, role


def collapse(v: dict) -> dict:
    """The scenes show top-level values only; a parent carries its children's capabilities and pains."""
    vals = v.get("values") or []
    kids = {}
    for x in vals:
        if x.get("parent"):
            kids.setdefault(x["parent"], []).append(x)
    top = []
    for x in vals:
        if x.get("parent"):
            continue
        ch = kids.get(x["id"], [])
        uniq = lambda key: list(dict.fromkeys((x.get(key) or []) + [i for c in ch for i in c.get(key) or []]))
        top.append(dict(x, children=ch, capabilities=uniq("capabilities"), pains=uniq("pains")))
    return dict(v, values=top)


# ── detail templates (opened in the side panel) ─────────────────────────────
def details(v: dict, launch: dict | None, loc) -> str:
    web = f"https://github.com/{v['product']['repo']}" if v.get("product", {}).get("repo") else None
    caps = {c["id"]: c for c in v.get("capabilities") or []}
    by_id = {s["id"]: s for s in (launch or {}).get("sources") or []}
    pains = {p["id"]: p for p in (launch or {}).get("pains") or []}
    out = []
    for x in v.get("values") or []:
        proof = "".join(f"<li>{e(p.get('claim'))} {loc(p, web) if (p.get('file') or p.get('url')) else ''}"
                        + (f"<br><code>$ {e(p.get('command'))}</code> → {e(p.get('output'))}" if p.get("command") else "") + "</li>"
                        for p in x.get("proof") or [])
        capl = "".join(f"<li>{e(caps.get(c, {}).get('name', c))} "
                       + " ".join(loc(ev, web) for ev in caps.get(c, {}).get("evidence") or []) + "</li>"
                       for c in x.get("capabilities") or [])
        pl = "".join(f"<li>{e(pains[p]['statement'])} ({authors(pains[p], by_id)} people)</li>" for p in x.get("pains") or [] if p in pains)
        kids = "".join(f"<li>{GLYPH.get(c.get('level'), '')} {e(c.get('outcome'))} <i>({e(c.get('level'))})</i>"
                       + "".join(f"<br><small>{e(q.get('claim'))} {loc(q, web) if (q.get('file') or q.get('url')) else ''}</small>" for q in c.get("proof") or [])
                       + "</li>" for c in x.get("children") or [])
        lr = (v.get("first_screen") or {}).get("lead_reason") if x["id"] in ((v.get("first_screen") or {}).get("lead") or []) else None
        why_lead = (f"<h4>Why it leads</h4><p>{e(lr.get('relevance'))}</p><p>Instead of {e((lr.get('differentiation') or {}).get('alternative'))}: "
                    f"{e((lr.get('differentiation') or {}).get('why'))}</p>") if lr else ""
        out.append(f"""<template id="d-{e(x['id'])}"><div class="act">{e(x['id'])} · {e(x.get('level'))}</div>
<h3>{e(x.get('outcome'))}</h3><p>{e(x.get('why'))}</p>{why_lead}
{f'<h4>Includes</h4><ul>{kids}</ul>' if kids else ''}
<h4>Proof</h4>{f'<ul>{proof}</ul>' if proof else '<p>No proof recorded.</p>'}
<h4>Capabilities</h4><ul>{capl}</ul>
<h4>Pain it answers</h4>{f'<ul>{pl}</ul>' if pl else '<p>None observed yet.</p>'}</template>""")
    for p in pains.values():
        people = {}
        for s in p.get("source_ids", []):
            if s in by_id:
                people.setdefault((by_id[s]["platform"], by_id[s]["author"].lower()), by_id[s])
        qs = "".join(f"<li>“{e(s['quote'])}” — {e(s['author'])}, <a href='{e(s['url'])}'>source</a></li>" if s.get("verbatim")
                     else f"<li><i>{e(s['quote'])} (paraphrase)</i> — {e(s['author'])}</li>" for s in people.values())
        wk = "".join(f"<li>{e(w.get('text'))}</li>" for w in p.get("workarounds") or [])
        out.append(f"""<template id="d-{e(p['id'])}"><div class="act">{e(p['id'])} · {len(people)} independent people · fit {e(p.get('fit'))}</div>
<h3>{e(p.get('statement'))}</h3><p>{e(p.get('fit_reason'))}</p><h4>In their words</h4><ul>{qs}</ul>
{f'<h4>What people do today</h4><ul>{wk}</ul>' if wk else ''}</template>""")
    return "\n".join(out)


# ── scene 1: VALUE constellation ────────────────────────────────────────────
def scene_value(v: dict, name: str) -> str:
    vals, role = ordered_values(v)
    W, H, cx, cy = 900, 470, 450, 250
    lead = [x for x in vals if role.get(x["id"]) == "lead"][:1]
    mid = [x for x in vals if role.get(x["id"]) in ("support", "trust")][:4]
    rest = [x for x in vals if x not in lead and x not in mid]
    pos = {}
    if lead:
        pos[lead[0]["id"]] = (cx, 70, 30, 21)
    # support/trust: up to four fixed slots, left and right of the centre, so labels never collide
    slots = [(cx - 250, cy - 70), (cx + 250, cy - 70), (cx - 330, cy + 40), (cx + 330, cy + 40)]
    for i, x in enumerate(mid):
        pos[x["id"]] = (*slots[i], 18, 16)
    n = len(rest)
    for i, x in enumerate(rest):
        px = cx - 360 + (720 * (i + 0.5) / max(1, n))
        pos[x["id"]] = (px, 408, 8, 12)
    svg = [f'<svg viewBox="0 0 {W} {H + 60}" role="img" aria-label="Value map">']
    svg.append(f'<text x="{cx}" y="{cy + 6}" text-anchor="middle" font-family="IBM Plex Mono,monospace" font-size="13" letter-spacing="3" fill="var(--muted)">{e(name.upper())}</text>')
    for x in vals:
        px, py, r, fs = pos[x["id"]]
        dim = 0.35 if x in rest else 0.7
        below = py + r + 2 * fs * 1.2 + 10          # under the two-line label
        svg.append(f'<line x1="{cx}" y1="{cy - 14 if py < cy else cy + 12}" x2="{px}" y2="{below if py < cy else py - r}" stroke="var(--rule)" stroke-width="{2 if x in lead else 1.2}" opacity="{dim}"/>')
    if rest:
        svg.append(f'<text x="{cx}" y="{378}" text-anchor="middle" font-family="IBM Plex Mono,monospace" font-size="10.5" letter-spacing="2" fill="var(--muted)">ALSO TRUE, DON\'T LEAD</text>')
    for x in vals:
        px, py, r, fs = pos[x["id"]]
        color = "var(--sage)" if role.get(x["id"]) == "lead" else ("var(--ink)" if x not in rest else "var(--muted)")
        width = 34 if x in lead else (26 if x in mid else 18)
        lines = wrap(x.get("label") or x.get("outcome"), width, 2)
        ly = py + r + fs + 2
        if x in rest and len(rest) > 5 and rest.index(x) % 2:   # stagger crowded bottom labels
            ly += 2 * round(fs * 1.2) + 4
        svg.append(f'<g class="hit" data-d="{e(x["id"])}">{node(px, py, r, x.get("level"), color)}'
                   f'<text class="lbl" x="{px}" y="{ly}" text-anchor="middle" font-family="Newsreader,Georgia,serif" '
                   f'font-size="{fs}" fill="{color if x not in rest else "var(--muted)"}">{tspans(px, lines, round(fs * 1.2))}</text></g>')
        if x.get("children"):
            svg.append(f'<text x="{px + r + 4}" y="{py + 4}" font-family="IBM Plex Mono,monospace" font-size="{max(10, fs - 5)}" fill="var(--muted)">+{len(x["children"])}</text>')
        if x in lead or x in mid:
            svg.append(f'<text x="{px}" y="{py - r - 8}" text-anchor="middle" font-family="IBM Plex Mono,monospace" font-size="10" letter-spacing="1.5" fill="var(--muted)">{e(role.get(x["id"], "").upper())}</text>')
    svg.append("</svg>")
    lead_txt = short(lead[0]["outcome"], 14) if lead else "No value can lead yet: none is demonstrated or supported."
    return (f'<section class="scene"><div class="act">1 · Value</div><h2>What {e(name)} gives a user</h2>'
            f'<p class="say">{e(lead_txt)}</p>' + "".join(svg)
            + '<div class="key"><span>● demonstrated</span><span>◐ supported</span><span>○ hypothesis</span>'
              '<span>size = role</span><span>+N = grouped values</span><span>click a node for its proof</span></div></section>')


# ── scene 2: PULL bridge ────────────────────────────────────────────────────
def scene_pull(v: dict, launch: dict | None) -> str:
    head = '<section class="scene"><div class="act">2 · Pull</div><h2>Which values meet real pain</h2>'
    if not launch or not launch.get("pains"):
        return head + '<p class="say">No market evidence yet. Run <code>/beacon</code> to find people describing the problem.</p></section>'
    vals, role = ordered_values(v)
    by_id = {s["id"]: s for s in launch.get("sources") or []}
    pains = sorted(launch["pains"], key=lambda p: -authors(p, by_id))
    answered = {pid for x in vals for pid in x.get("pains") or []}
    shown = [x for x in vals if x.get("pains")] + [x for x in vals if not x.get("pains")][:3]
    rowh, W = 50, 900
    H = max(len(shown), len(pains) + 1) * rowh + 50
    lx, rx = 330, W - 330
    ly = {x["id"]: 50 + i * rowh for i, x in enumerate(shown)}
    ry = {p["id"]: 50 + i * rowh for i, p in enumerate(pains)}
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Values linked to observed pains">',
         f'<text x="{lx}" y="16" text-anchor="end" font-family="IBM Plex Mono,monospace" font-size="10.5" letter-spacing="2" fill="var(--muted)">WHAT WE PROVIDE</text>',
         f'<text x="{rx}" y="16" font-family="IBM Plex Mono,monospace" font-size="10.5" letter-spacing="2" fill="var(--muted)">WHAT PEOPLE NEED</text>']
    for x in shown:
        for pid in x.get("pains") or []:
            if pid in ry:
                w = 1.5 + min(7, 0.7 * authors(next(p for p in pains if p["id"] == pid), by_id))
                y1, y2 = ly[x["id"]], ry[pid]
                s.append(f'<path d="M{lx + 10},{y1} C{lx + 120},{y1} {rx - 120},{y2} {rx - 10},{y2}" fill="none" stroke="var(--sage)" stroke-width="{w:.1f}" opacity=".75"/>')
    for x in shown:
        y = ly[x["id"]]
        col = "var(--ink)" if x.get("pains") else "var(--muted)"
        s.append(f'<g class="hit" data-d="{e(x["id"])}"><text class="lbl" x="{lx - 12}" y="{y + 5}" text-anchor="end" font-family="Newsreader,Georgia,serif" '
                 f'font-size="{17 if role.get(x["id"]) == "lead" else 15}" fill="{col}">{e(x.get("label") or short(x.get("outcome"), 8, 32 if role.get(x["id"]) == "lead" else 36))}</text>'
                 f'{node(lx + 4, y, 6, x.get("level"), col)}</g>')
    for p in pains:
        y = ry[p["id"]]
        n = authors(p, by_id)
        col = "var(--ink)" if p["id"] in answered else "var(--cinnabar)"
        s.append(f'<g class="hit" data-d="{e(p["id"])}"><circle cx="{rx - 4}" cy="{y}" r="6" fill="{col}"/>'
                 f'<text class="lbl" x="{rx + 10}" y="{y + 5}" font-family="Newsreader,Georgia,serif" font-size="15" fill="{col}">{e(short(p.get("statement"), 6))}</text>'
                 f'<text x="{rx + 10}" y="{y + 20}" font-family="IBM Plex Mono,monospace" font-size="10.5" fill="{"var(--muted)" if p["id"] in answered else "var(--cinnabar)"}">{n} people{"" if p["id"] in answered else " · no mapped value"}</text></g>')
        if p["id"] not in answered:
            s.append(f'<path d="M{rx - 70},{y} L{rx - 12},{y}" stroke="var(--cinnabar)" stroke-width="1.3" stroke-dasharray="2 4"/>')
    s.append("</svg>")
    n_ans = sum(1 for p in pains if p["id"] in answered)
    say = f"{n_ans} of {len(pains)} observed pains are answered by a value" + (
        f"; {len(pains) - n_ans} (red) by none." if n_ans < len(pains) else ".")
    return head + f'<p class="say">{e(say)}</p>' + "".join(s) + '<div class="key"><span>line width = independent people</span><span>red = pain with no mapped value</span><span>click for quotes</span></div></section>'


# ── scene 3: COVERAGE matrix ────────────────────────────────────────────────
def scene_coverage(v: dict) -> str:
    vals, role = ordered_values(v)
    caps = v.get("capabilities") or []
    cov = {c["id"]: {vid for x in vals for vid in [x["id"]] if c["id"] in (x.get("capabilities") or [])} for c in caps}
    cols = vals[:10]
    cw, rh, lw = 62, 34, 300
    W = lw + cw * len(cols) + 140
    H = 110 + rh * len(caps)
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Which features support which values">']
    for j, x in enumerate(cols):
        tx = lw + j * cw + cw / 2
        col = "var(--sage)" if role.get(x["id"]) == "lead" else "var(--ink)"
        s.append(f'<g class="hit" data-d="{e(x["id"])}"><text transform="translate({tx},96) rotate(-35)" font-family="Newsreader,Georgia,serif" font-size="13" fill="{col}">{e(x.get("label") or short(x.get("outcome"), 3))}</text></g>')
    for i, c in enumerate(caps):
        y = 118 + i * rh
        used = cov.get(c["id"]) & {x["id"] for x in cols}
        col = "var(--ink)" if cov.get(c["id"]) else "var(--cinnabar)"
        name = short(c.get("name"), 5)
        name = name if len(name) <= 38 else name[:37] + "…"
        s.append(f'<text x="{lw - 14}" y="{y + 5}" text-anchor="end" font-family="Newsreader,Georgia,serif" font-size="14" fill="{col}">{e(name)}</text>')
        s.append(f'<line x1="{lw}" y1="{y + 16}" x2="{lw + cw * len(cols)}" y2="{y + 16}" stroke="var(--rule)"/>')
        for j, x in enumerate(cols):
            if x["id"] in used:
                s.append(f'<circle cx="{lw + j * cw + cw / 2}" cy="{y}" r="8" fill="{"var(--sage)" if role.get(x["id"]) == "lead" else "var(--ink)"}"/>')
            else:
                s.append(f'<circle cx="{lw + j * cw + cw / 2}" cy="{y}" r="2" fill="var(--rule)"/>')
        if not cov.get(c["id"]):
            s.append(f'<text x="{lw + cw * len(cols) + 12}" y="{y + 5}" font-family="IBM Plex Mono,monospace" font-size="11" fill="var(--cinnabar)">NO MAPPED VALUE</text>')
    s.append("</svg>")
    orphans = [c for c in caps if not cov.get(c["id"])]
    say = (f"{len(orphans)} of {len(caps)} capabilities have no mapped value, so they don't belong in the story yet."
           if orphans else "Every capability supports at least one value.")
    more = f" Showing the first {len(cols)} of {len(vals)} values." if len(vals) > len(cols) else ""
    return (f'<section class="scene"><div class="act">3 · Coverage</div><h2>What each feature is for</h2><p class="say">{e(say + more)}</p>'
            + "".join(s) + "</section>")


# ── scene 4: STORY funnel ───────────────────────────────────────────────────
def scene_story(v: dict) -> str:
    fs = v.get("first_screen") or {}
    vals = {x["id"]: x for x in v.get("values") or []}
    caps = {c["id"]: c for c in v.get("capabilities") or []}
    if not fs:
        return ""
    f = ['<div class="funnel">']
    for part, words in (("lead", 12), ("support", 10), ("trust", 10)):
        for vid in fs.get(part) or []:
            x = vals.get(vid, {})
            if len(f) > 1:
                f.append('<div class="arrow">↓</div>')
            f.append(f'<div class="fn {part}" data-d="{e(vid)}"><span class="r">{part}</span>{e(x.get("label") or short(x.get("outcome"), words))}</div>')
    if fs.get("advanced"):
        f.append('<div class="arrow">↓</div>')
        f.append('<div class="fn adv"><span class="r">advanced, don\'t lead</span>'
                 + " · ".join(e(short(caps.get(a["capability"], {}).get("name", a["capability"]), 4)) for a in fs["advanced"]) + "</div>")
    lr = fs.get("lead_reason") or {}
    alt = (lr.get("differentiation") or {}).get("alternative")
    if alt and len(f) > 1:
        f.insert(2, f'<div class="because">chosen over <b>{e(short(alt, 8))}</b></div>')
    f.append("</div>")
    stop = ""
    if fs.get("stop_saying"):
        stop = ('<div class="stop"><span class="r">✕ STOP SAYING</span>'
                + "".join(f'<div><s>“{e(short(x.get("claim"), 8))}”</s></div>' for x in fs["stop_saying"]) + "</div>")
    return (f'<section class="scene"><div class="act">4 · Story</div><h2>What the first screen should say</h2>'
            f'<p class="say">Lead with why people choose it; proof sets how strongly to say it; drop what the evidence doesn\'t support.</p>'
            f'<div class="storyrow">{"".join(f)}{stop}</div></section>')


# ── scene 5: MOVE ───────────────────────────────────────────────────────────
def scene_move(launch: dict | None) -> str:
    head = '<section class="scene"><div class="act">5 · Move</div><h2>The one next move</h2>'
    ex = (launch or {}).get("experiment")
    if not ex:
        return head + '<p class="say">No experiment yet. <code>/beacon</code> proposes one, grounded in the pull above.</p></section>'
    aud = next((a for a in launch.get("audiences") or [] if a.get("id") == ex.get("audience")), {})
    sc = ex.get("success") or {}
    steps = [("who", short(aud.get("who"), 12)), ("where", short(ex.get("channel"), 12)),
             ("say", short(ex.get("hook"), 12)), ("ask", short(ex.get("cta"), 14)),
             ("wait", f"{sc.get('window_hours', '?')} hours")]
    out = ['<div class="move">']
    for i, (r, t) in enumerate(steps):
        if i:
            out.append('<div class="arrow">↓</div>')
        out.append(f'<div class="mv"><span class="r">{r}</span>{e(t)}</div>')
    out.append('<div class="arrow">↓</div>')
    out.append(f'<div class="mv goal"><span class="r">success</span>{e(short(sc.get("threshold"), 10))}</div></div>')
    return head + "".join(out) + "</section>"


def render_v2(value: dict, launch: dict | None, evidence_html: str, loc, base_css: str) -> str:
    name = value.get("product", {}).get("name", "this project")
    value = collapse(value)
    body = [scene_value(value, name), scene_pull(value, launch), scene_coverage(value), scene_story(value), scene_move(launch)]
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Beacon · {e(name)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,600;1,6..72,400&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>{base_css}{CSS}</style></head><body><main>
<div class="fig">Beacon · {e(name)} · {e(value.get('product', {}).get('date', ''))}</div>
{"".join(body)}
<details class="evidence"><summary>See the evidence →</summary>{evidence_html}</details>
</main>
<aside id="panel" aria-live="polite"><button class="x" aria-label="Close">×</button><div class="body"></div></aside>
{details(value, launch, loc)}
<script>{JS}</script></body></html>"""
