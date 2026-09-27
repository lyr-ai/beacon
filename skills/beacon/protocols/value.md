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

## Phase 0: One primary audience

Name the one group this run is for (`audience`): specific enough that you
could find them ("teams self-hosting open models behind their own API"), not
"developers". Values, the lead and the first screen are all judged for this
audience. If the project clearly serves other groups, list them in
`other_audiences`; they don't change this run's map.

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
| `demonstrated` | ● | ≥1 **confirmed** proof, which means something was **executed**: a command (a test, a benchmark, a script) you ran, with its exit code and output, or a CI run that passed at a named commit (its URL) |
| `supported` | ◐ | code, docs or tests that implement or assert the behaviour, read but not executed (**observed**) |
| `hypothesis` | ○ | an outcome inferred from the capabilities; say it's a guess, and why it's worth testing |

**A test that exists is not a test that passed.** Reading a test file is
`observed` evidence, and makes a value `supported`. To call it
`demonstrated`, run the test (if it is safe and cheap), or cite a CI run that
passed at a named commit. If you can do neither, the value is `supported`,
however good the test looks.

Write outcomes that the proof actually supports. "Prevents a late
historical record from replacing the current value" can be demonstrated.
"Reduces production incidents" can't, unless you have incident data; if you
believe it, it's a `hypothesis`.

### At most 7 top-level values

A map with a dozen values reads as a feature list again. Keep **at most 7
top-level values**. When there are more, group related ones under a parent
that states the shared outcome in the user's terms (`parent: "V2"`); the
children stay in the map and open on demand. Group by the outcome a user
would recognize, not by module. A child can't have children of its own, and
a parent's level is its own proof's level, not its best child's.

## Phase 3: Connect to the outside (if `.beacon/launch.json` exists)

For each value, list the Beacon **pains** it answers (`pains: ["P1"]`).
Capabilities with no mapped value, and values that answer no observed pain,
are findings in their own right:
- a capability with no mapped value may not deserve airtime (it may still help users; the map just found no evidence that it does);
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
- `lead`: one value, chosen by what makes the audience choose this project,
  **not** by which proof is strongest. Proof decides how strongly a value
  can be said; it doesn't decide what is worth saying first. Pick the value
  that passes both:
  - **relevance**: it answers the audience's core job or pain (when
    `launch.json` exists, prefer a value linked to the strongest pain);
  - **differentiation**: it explains why this project and not the obvious
    alternative, which you name ("instead of grep", "instead of a hosted
    API").

  Record both in `lead_reason`. A value that is easy to prove but that
  any alternative also offers, or that is a count rather than an outcome,
  is not a lead. The lead can't be a `hypothesis`: if the most relevant,
  differentiating value is only a guess, lead with the best `supported`
  value and say so in `lead_reason`.
- `support`: two or three top-level values (fewer only if the map has fewer);
- `trust`: one or two top-level values that make it safe to adopt
  (correctness, portability, compatibility, stability);
- the remaining top-level values are "also true": kept, not led with;
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
python3 "$SKILL_DIR/scripts/render.py" --value .beacon/value.json -o .beacon/report.html
# if .beacon/launch.json exists, the same report also includes "Where is the pull?"
```

Tell the user:
- the audience, the lead value, why it leads (relevance, differentiation) and its proof;
- how many values are demonstrated, supported and hypothesis;
- capabilities with no mapped value;
- values that answer no observed pain;
- any `stop_saying` items.
