---
name: beacon
description: Evidence-driven go-to-market for a developer project. `/beacon` checks that the positioning can be stated with evidence, maps who has the problem, mines public pain in people's own words (Hacker News, GitHub issues, Reddit), and proposes ONE next distribution experiment (one audience × one message × one channel × one call to action) with a success criterion. It writes .beacon/launch.json and a visual report. `/beacon record` logs an experiment's results so the next launch doesn't start from zero. Use when the user asks how to launch, distribute or find users for a project.
---

# Beacon: find the people who should see this

You run a go-to-market *investigation*. The output is **one next
experiment**, backed by evidence of who has the problem and where they
talk about it. It is not a launch checklist, and not a pile of marketing
copy. "Post on Reddit, HN, LinkedIn and write a blog" is the failure this
skill exists to prevent.

`SKILL_DIR` means the directory containing this file.

## Ground rules

- **People's words are evidence; your summaries are not.** A pain counts
  because people said it. Quote them verbatim, with URL, author and date.
  Text you only saw through a summarizing fetch tool is recorded with
  `"verbatim": false` and shown as a paraphrase.
- **Count people, not posts.** Five comments by one author are one voice.
  Strength is the number of *independent authors*.
- **Look for counter-evidence too.** People who say the problem is solved,
  rare or not worth a tool go in `counter_evidence`.
- **No fake precision.** No "product-market fit" or "demand" percentages or
  scores. Say what was observed ("9 independent authors across HN and GitHub
  describe…") and what wasn't ("no one described paying for a fix").
- **Read-only.** Write only inside `.beacon/`. Never post, comment or message
  anyone. The user runs the experiment.
- **One experiment.** Everything else goes to `not_this_round`.

## Phase 0: Context

Read what's already known:
- `.heed/project.json` (a goal confirmed with Heed), if present; otherwise
  the README, its first screen especially, and the docs;
- `.beacon/history/*.json`: past experiments and their results. Don't
  repeat an experiment that already failed without saying what's different
  this time.

## Phase 1: Positioning gate

Write five statements, each with evidence from the repo (`file:line`) or a
URL:

| Field | Question |
|---|---|
| `problem` | What situation hurts, in the user's terms? |
| `failure` | What concretely goes wrong without this project? |
| `product` | What does it do about that failure? |
| `proof` | What shows it works today (a release, tests, a demo, users)? |
| `boundary` | What doesn't it do? |

If any field can't be stated with evidence, set `"gate": "stop"`, list what's
missing in `gate_missing`, render the report and **stop**. A project that
can't say what it sells isn't ready for go-to-market, and that is a useful
result.

## Phase 2: Queries

From `problem` and `failure`, write 6–10 search queries **in the language a
sufferer would use**, not the product's vocabulary. For example, "agent
remembers old address" rather than "temporal state management". Include
queries for workarounds ("delete old memories", "overwrite memory") and for
alternatives. Record every query in `queries`.

## Phase 3: Pain evidence

1. Verbatim sources, collected by script:
   ```bash
   mkdir -p .beacon
   python3 "$SKILL_DIR/scripts/search.py" "<query 1>" "<query 2>" ... \
       --since <about 18 months ago> --per-query 15 > .beacon/sources.jsonl
   ```
2. Reddit and other sites, via your web search (for example
   `site:reddit.com <query>`). Open the promising threads. Record each with
   `"verbatim": false` unless you copied the text exactly.
3. **Read** the sources. Keep only the ones that actually describe the
   problem, a workaround, or a request close to it. Drop keyword accidents.
4. Cluster the kept sources into 2–6 **pains**. For each, record:
   - one statement, in users' words;
   - its `source_ids`;
   - `language`: 2–4 short verbatim phrases people used;
   - `workarounds`: what people do today, with sources;
   - `fit`: `high`, `partial` or `none` against the project's boundary,
     with a reason.
5. Record `counter_evidence`.

`validate.py` counts independent authors per pain from the sources. Don't
type the counts yourself.

## Phase 4: Audiences

Two to four **specific** audiences, never "AI developers". For each, record:
- who they are and what they're building;
- the failure that would make them care (the `trigger`);
- where they talk (`where`, from where their sources came from);
- their own `language`;
- `fit`: strong, partial or weak;
- the `source_ids` behind it.

## Phase 5: One experiment

Pick **one** audience, **one** hook, **one** channel and **one** call to action.
- `hypothesis`: what you expect and why, citing pains and sources.
- `hook` and `message`: the draft post, in the audience's language. It
  leads with the pain, not the product, and is honest about the project's
  limits.
- `channel` and `why_channel`: evidence that this audience talks about this
  pain there.
- `cta`: what you ask readers to do. Prefer "how do you handle this
  today?" over "star my repo" when the goal is to learn.
- `success`: an observable signal, a threshold and a window. For example,
  "≥3 replies describing their own workaround within 72h". Also record
  what would count as failure.
- `not_this_round`: the other channels and hooks, each with a reason.

Then write `.beacon/history/<date>-<channel-slug>.json` with the
experiment and `"results": null`.

## Phase 6: Validate, render, tell

```bash
python3 "$SKILL_DIR/scripts/validate.py" .beacon/launch.json
python3 "$SKILL_DIR/scripts/render.py" .beacon/launch.json -o .beacon/report.html
open .beacon/report.html
```

Fix every validation error. Then tell the user, briefly:
- the gate result;
- the strongest pain, with its independent-author count;
- the one experiment;
- the success threshold;
- the command to record results afterwards.

## `/beacon record`

After the experiment's window has passed, ask the user for what happened.
- **Numbers:** views, comments, upvotes, repo visits, stars, installs,
  issues. `null` means unknown; don't guess.
- **Signals:** what people actually said, quoted with links.

Write them into the history file as `results` and `signals`, and add a
one-line `decision`: what this changes about the next round. Where the
funnel broke is the most useful thing to record:
- **exposure:** nobody saw it;
- **engagement:** people saw it but didn't respond;
- **try:** people responded but didn't visit or install;
- **use:** people installed but didn't come back.
