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

## Run 2 result

(to be filled in after the run)
