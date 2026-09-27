# `.beacon/launch.json` format (version 1)

```json
{
  "version": 1,
  "product": {"name": "typedmem", "repo": "lyr-ai/typedmem", "date": "2026-09-27"},
  "gate": "pass",
  "gate_missing": [],
  "positioning": {
    "problem":  {"text": "...", "evidence": [{"file": "README.md", "line": 5}]},
    "failure":  {"text": "...", "evidence": [{"url": "https://..."}]},
    "product":  {"text": "...", "evidence": [...]},
    "proof":    {"text": "...", "evidence": [...]},
    "boundary": {"text": "...", "evidence": [...]}
  },
  "queries": [{"query": "agent remembers outdated facts", "platforms": ["hn", "github", "reddit"]}],
  "sources": [
    {"id": "hn-47374335", "platform": "hn", "url": "https://news.ycombinator.com/item?id=47374335",
     "author": "mohitbadi", "date": "2026-03-14", "quote": "exact words from the source", "verbatim": true}
  ],
  "pains": [
    {"id": "P1", "statement": "Old facts keep coming back after they change",
     "source_ids": ["hn-47374335", "gh-..."],
     "language": [{"text": "memory went stale", "source_id": "hn-47374335"}],
     "workarounds": [{"text": "Delete the old memory by hand", "source_ids": ["gh-..."]}],
     "fit": "high", "fit_reason": "Exactly the late/changed value case"}
  ],
  "counter_evidence": [{"claim": "Some say a timestamp filter is enough", "source_ids": ["..."]}],
  "audiences": [
    {"id": "A1", "who": "Solo developers building personal/coding agents with long-lived memory",
     "building": "...", "trigger": "...", "where": ["HN Show HN threads", "GitHub"],
     "language": ["..."], "fit": "strong", "source_ids": ["..."]}
  ],
  "experiment": {
    "audience": "A1", "hook": "...", "message": "the draft post",
    "channel": "Hacker News (comment in relevant threads)", "why_channel": [{"reason": "...", "source_ids": ["..."]}],
    "cta": "How do you handle this today?",
    "hypothesis": "...",
    "success": {"signal": "replies describing their own workaround", "threshold": ">= 3", "window_hours": 72,
                "failure": "0-1 substantive replies"},
    "not_this_round": [{"item": "LinkedIn", "reason": "..."}],
    "history_file": ".beacon/history/2026-09-27-hn.json"
  }
}
```

## Rules (checked by `validate.py`)

- `gate`: `pass` or `stop`.
  - `stop` needs `gate_missing` and no `experiment`.
  - `pass` needs all five positioning fields, each with a `text` and ≥1
    evidence locator (`file` + `line` that exist, or a `url`).
- `sources[]`: unique `id`, and `platform` ∈ `hn | github | reddit | web`.
  Needs `url`, `author`, `date` and `quote`, and `verbatim` must be a boolean.
  When `.beacon/sources.jsonl` holds the source, a `verbatim: true` quote
  must appear in its raw text.
- `pains[]`: ≥1 `source_id`, all of them existing, and `fit` ∈
  `high | partial | none` with a `fit_reason`.
  - A `language` phrase must appear in the quote of the source it cites.
  - Independent authors are counted by the validator, never typed in.
- `audiences[]`: 2–4, each with `fit` ∈ `strong | partial | weak`. A generic
  `who` ("developers", "AI developers", "everyone") is rejected.
- `experiment` (gate pass): exactly one `channel` (a string) and all
  fields; `success` needs a `signal`, `threshold`, `window_hours` and
  `failure`; `not_this_round` needs ≥1 item.
- No key anywhere may be a score or percentage (`score`, `pmf`, `percent`,
  `probability`). Say what was observed instead.

---

# `.beacon/value.json` format (version 1), written by `/beacon value`

```json
{
  "version": 1,
  "product": {"name": "typedmem", "repo": "lyr-ai/typedmem", "date": "2026-09-27"},
  "problem": {"text": "Facts an agent relies on change over time.", "evidence": [{"file": "README.md", "line": 5}]},
  "capabilities": [
    {"id": "state", "name": "set / get / history", "evidence": [{"file": "typedmem/agent.py", "line": 236}]}
  ],
  "values": [
    {"id": "V1", "outcome": "Know which value is current without deleting the old one",
     "why": "The agent doesn't act on stale state", "capabilities": ["state"], "level": "demonstrated",
     "proof": [{"level": "confirmed", "kind": "command", "claim": "LongMemEval KU history 0/11 → 11/11",
                "command": "reliagent-bench@df0ebc6 external/run_longmemeval_ku.py", "exit_code": 0, "output": "v9_states 65/65"}],
     "pains": ["P1"]}
  ],
  "first_screen": {
    "lead": ["V1"], "support": ["V2"], "trust": ["V3"],
    "advanced": [{"capability": "profiles", "reason": "Depth, but no observed pain"}],
    "stop_saying": [{"claim": "Contract-driven memory", "file": "README.md", "line": 105, "reason": "No value or pain supports leading with it"}]
  }
}
```

## Rules (checked by `validate.py --value`)

- Every capability has an `id`, a `name`, and ≥1 locator (`file` + `line` that exist, or a `url`).
- Every value has an `outcome`, a `why`, a `level` ∈ `demonstrated | supported | hypothesis`, and `capabilities` that exist.
  - `demonstrated`: ≥1 `proof` item with `level: confirmed` and a locator.
  - `supported`: every capability it relies on has a locator (already required), and no `confirmed` proof is claimed.
  - `hypothesis`: no proof required.
- `pains` must exist in `.beacon/launch.json`, when it is present.
- `first_screen` references existing ids. `lead` has exactly one value, and it can't be a `hypothesis`. Every `stop_saying` item has a locator.
- No score-like keys.
