# `/beacon value` v0.1: pre-registered re-run

Written 2026-09-27, before any protocol change. Run 1 is the frozen v0 protocol on
four repos Beacon had never seen (ripgrep, vLLM, Excalidraw, LongMemEval). It passed
its generality criteria, but showed three problems that change conclusions or the
first read. v0.1 changes only these three. Multiple audiences (d) and external proof
(e) are recorded requirements, not part of v0.1.

## What changes

a. **Demonstrated means it was run.** A test file that exists is not a test that
   passed. `demonstrated` needs a proof that was executed: a command run this session
   with its exit code and output, or a CI run that passed at a named commit. A test
   or code locator alone makes a value `supported`.

b. **Proof decides how strongly to say it, not what to lead with.** The lead is
   chosen by relevance (does it answer the chosen audience's core job or pain?) and
   differentiation (why this project over the obvious alternative, named). Proof then
   sets the level. Each run names one primary audience.

c. **At most 7 top-level values.** Related values are grouped under a parent and are
   shown on demand. The first screen has 1 lead, 2–3 support, and 1–2 trust values.

The protocol text must not name any of the four repos or their features, so the
re-run stays blind.

## Run 1 (v0), for comparison

| Repo | Values | Lead |
|---|---|---|
| ripgrep | 12 (8 demonstrated / 3 supported / 1 hypothesis) | Only files you work on (gitignore-aware), demonstrated from test files read, not run |
| vLLM | 12 (1 / 10 / 1) | "Your model's architecture is very likely already implemented" (registry count) |
| Excalidraw | 12 (7 / 4 / 1) | Real-time collaboration; the informal hand-drawn look was V12, a hypothesis |
| LongMemEval | 5 (0 / 4 / 1) | Per-ability accuracy breakdown; the run said a product-style map fits only partly |

## Expected in run 2 (pass criteria)

Run the same four repos with the same prompt (the same repos, commit and blindness
rules; the only addition is permission to query CI read-only), plus TypedMem.

1. **ripgrep**: the lead is a reason a grep user switches (speed, or respecting
   ignore files by default). It is not a narrow feature (encodings, PCRE2, JSON output,
   config files).
2. **vLLM**: the lead is not model or architecture coverage. It is a serving value
   (throughput or memory efficiency, or self-hosted OpenAI-compatible serving).
3. **Excalidraw**: the informal hand-drawn identity is the lead or a support value,
   at `supported` or above, not a hypothesis under "also true".
4. **LongMemEval**: it still says it isn't a typical product, and it doesn't invent
   product value. Nothing is `demonstrated` unless something was actually run.
5. **TypedMem**: the lead is unchanged ("know which value is current, without
   deleting the old one") and still `demonstrated`.
6. **All**: every map validates. There are at most 7 top-level values. Every
   `demonstrated` value carries a run or CI proof, and one per repo is spot-checked
   against the real command or CI run.

One round only. A failure is recorded here as a failure, not fixed and re-run until
it passes. After run 2, `/beacon value` is frozen again.

## Run 2 result (2026-09-27)

Five fresh agents ran the v0.1 protocol: four blind, on the same clones at the same
commits (ripgrep 3fce3b5, vLLM e790015, Excalidraw 02fc9f3, LongMemEval 9e0b455),
and one on TypedMem, which was allowed to run its own tests. Every CI run cited was
checked with `gh` against the commit.

| Repo | Audience | Lead (level) | Chosen over | Values: demonstrated / supported / hypothesis (top-level + grouped) |
|---|---|---|---|---|
| ripgrep | Developers searching large source trees from the terminal | Matches only from files you work on (●) | `grep -r`, `git grep` | 10 / 1 / 0 (7 + 4) |
| vLLM | Platform teams self-hosting open-weight LLMs behind an API | Serve many concurrent requests from each GPU (◐) | Hugging Face `generate()` behind your own server | 6 / 9 / 1 (7 + 9) |
| Excalidraw | Product teams embedding a diagram canvas in a React app | A complete, familiar sketch-style editor from one component (●) | a low-level canvas library, or a hosted iframe | 7 / 3 / 1 (7 + 4) |
| LongMemEval | Teams building a memory layer who must measure it | Which kind of memory fails, not one score (◐) | needle-in-a-haystack tests, ad-hoc transcripts | 0 / 6 / 1 (5 + 2) |
| TypedMem | Python developers whose agents keep changing facts | Know which value is current, without losing the old ones (●) | overwrite on update, or append and let the agent pick | 10 / 1 / 0 (7 + 4) |

| # | Criterion | Result |
|---|---|---|
| 1 | ripgrep leads with a reason to switch | **Pass.** It leads with ignore-aware search, chosen over `grep -r`. Speed is support, at ◐, because its only evidence is the README's unexecuted benchmark tables. |
| 2 | vLLM doesn't lead with model coverage | **Pass.** It leads with throughput per GPU. The registry count is now a support value, and `lead_reason` states that the repo has no evidence of an advantage over peer engines. |
| 3 | Excalidraw's hand-drawn identity is lead or support, ≥ ◐ | **Pass on the letter, with a caveat.** "Sketch-style" is in the demonstrated lead. But the run chose the React-embedding audience, so the lead's difference is "a full editor in one component". The explicit claim that the hand-drawn look makes people sketch more freely is still a hypothesis (V1c, grouped under the lead). The audience choice drove this, not proof strength. |
| 4 | LongMemEval stays honest | **Pass.** 0 demonstrated (no CI, and nothing could be run). It says it is a benchmark, not a product, and its stop-saying list names six README instructions that don't match the code. |
| 5 | TypedMem's lead is unchanged and ● | **Pass.** The proof is now executed: `pytest tests/test_state.py` gives 53 passed, and the committed LongMemEval result was read with `git show`. It also found two new stop-saying items: README:207 (ConflictPolicy on every state change) and README:281 (HTTP is the "same surface"). Both were checked and are true. |
| 6 | Structure | **Partial.** Every run has ≤7 top-level values, and every ● value carries a run or a CI job at the named commit (spot-checked). But Excalidraw put V3 in both support and trust, and the v0.1 validator allowed it. That is an enforcement gap in (c), now closed ("a value has one role"). Excalidraw's map fails the fixed validator, and it was not re-run. |

### Found in run 2 (not fixed; v0.1 is frozen)

f. **A whole-suite CI run inflates `demonstrated`.** Rule (a) moved the inflation
   rather than removing it. One passing run made 10 of ripgrep's 11 values ●, and one
   made 7 of Excalidraw's. vLLM's run did better by citing the specific job for each
   value. A likely fix: a CI proof names the test that asserts this outcome and the job
   that ran it (not skipped). This needs its own round.

g. **One audience is forced onto a two-product repo.** Excalidraw is both the npm
   component and excalidraw.com. This is the multi-audience requirement (d) again,
   still deferred.

h. **Published benchmarks have no level.** ripgrep's speed and vLLM's throughput are
   the projects' best-known values, and both sit at ◐. This is external proof (e),
   still deferred.

i. Smaller issues: proof `kind` has no defined vocabulary. With no `launch.json`, the
   validator's "values answering no observed pain" lists every value, which is noise.

## Decision

v0.1 (a, b, c, plus the one-role check) is kept and `/beacon value` is frozen again.
Items f–i are recorded; none is built without a new round designed for it.
