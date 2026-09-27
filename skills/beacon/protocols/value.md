# Beacon value: what does this project give a user, and why should they care?

Read `SKILL.md` first for the shared ground rules.

A feature list is not value. This mode builds a **value map**, one chain per
value:

```text
PROBLEM  →  CAPABILITY  →  USER OUTCOME  →  WHY IT MATTERS  →  PROOF
```

It also records **how strongly each value can be claimed**, so that launch
messages, READMEs and posts never say more than the evidence allows.

This is different from Heed's `goal`. `goal` is what the project says it
wants to become. `value` is what a stranger actually gets from it today.

## Phase 1: Capabilities (inside)

List the project's capabilities from its own evidence. If
`.heed/project.json` exists, start from its confirmed capabilities.
Otherwise read the README, the docs and the code. Each capability gets an
`id`, a `name`, and a code or doc locator (`file:line`).

## Phase 2: Values

For each distinct **user outcome** the capabilities produce, write one
value:
- **outcome**, in the user's terms: "Know which value is current without
  deleting the old one". Not "set/get/history".
- **why it matters**: the failure it prevents or the job it enables.
  "Your agent doesn't act on stale state."
- **capabilities**: the capability ids that deliver it.
- **level**: how strongly it can be claimed.

| Level | Glyph | Needs |
|---|---|---|
| `demonstrated` | ● | ≥1 **confirmed** proof: a test that exercises the outcome, a benchmark result, or a reproducible command with its output |
| `supported` | ◐ | ≥1 **observed** code or doc locator for each capability it relies on; no outside measurement |
| `hypothesis` | ○ | nothing; say it's a guess, and why it's worth testing |

Write outcomes that the proof actually supports. "Prevents a late
historical record from replacing the current value" can be demonstrated.
"Reduces production incidents" can't, unless you have incident data; if you
believe it, it's a `hypothesis`.

## Phase 3: Connect to the outside (if `.beacon/launch.json` exists)

For each value, list the Beacon **pains** it answers (`pains: ["P1"]`).
Capabilities that support no value, and values that answer no observed pain,
are findings in their own right:
- a capability that supports no value may not deserve airtime;
- a value that answers no observed pain is not yet a message, whatever its
  level.

## Phase 4: Feature → value coverage

The validator derives a coverage matrix from each value's `capabilities`:
features × values. Read it for two signals:
- several features all serving one value ("more configurable") suggests
  depth that doesn't add a new reason to care;
- a small feature carrying a large outcome suggests something to lead with.

## Phase 5: First-screen hierarchy

Recommend what the README's first screen (and any post) should say, in
order:
- `lead`: one value, the one with the strongest proof *and* the strongest
  pain link;
- `support` and `trust`: one or two values each;
- `advanced`: capabilities to keep but not lead with, each with a reason;
- `stop_saying`: claims currently made (in the README, docs or posts) that
  the value map doesn't support, each with the locator where the claim is
  made.

Each entry references value or capability ids.

## Phase 6: Write, validate, render

Write `.beacon/value.json` (format: `SKILL_DIR/format.md`, the "value.json"
section), then:

```bash
python3 "$SKILL_DIR/scripts/validate.py" --value .beacon/value.json
python3 "$SKILL_DIR/scripts/render.py" .beacon/launch.json -o .beacon/report.html   # value.json is picked up automatically
```

Tell the user:
- the lead value and its proof;
- how many values are demonstrated, supported and hypothesis;
- capabilities that support no value;
- values that answer no observed pain;
- any `stop_saying` items.
