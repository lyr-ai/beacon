---
name: beacon
description: Evidence-driven go-to-market for a developer project. `/beacon value` maps what the project actually gives a user: problem → capability → user outcome → proof, each value labelled demonstrated, supported or hypothesis, plus a recommended first-screen hierarchy. `/beacon` (launch) checks the positioning, mines public pain in people's own words (Hacker News, GitHub issues, Reddit) and proposes ONE next distribution experiment. `/beacon record` logs an experiment's results and reply quality. Writes into .beacon/ and renders a visual report. Use when the user asks what a project's value is, how to launch or position it, or how to find users.
---


# Beacon: find the people who should see this

You run a go-to-market *investigation*. The output is **one next
experiment**, backed by evidence of who has the problem and where they
talk about it. It is not a launch checklist, and not a pile of marketing
copy. "Post on Reddit, HN, LinkedIn and write a blog" is the failure this
skill exists to prevent.

`SKILL_DIR` means the directory containing this file.

## Modes

| Command | Question | Protocol | Output |
|---|---|---|---|
| `/beacon value` | What value does this project create, and what can we honestly claim? | `protocols/value.md` | `.beacon/value.json` |
| `/beacon` or `/beacon launch` | Where is the pull, and what is the one next experiment? | `protocols/launch.md` | `.beacon/launch.json` |
| `/beacon record` | What did the last experiment produce? | `protocols/record.md` | `.beacon/history/*.json` |

Run `value` before `launch` when you can: launch messages may only claim values that `value` found demonstrated or supported. Every mode re-renders `.beacon/report.html`.

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

