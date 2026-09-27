# Beacon record: log what an experiment produced

Read `SKILL.md` first.


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

Also record each reply's **quality level**:

| Level | Meaning |
|---|---|
| L0 | no response |
| L1 | thanks or 👍 only |
| L2 | discusses, disagrees with or asks about the substance |
| L3 | asks about implementation, tries the project, or cites it in their own design |

What matters is L2 and above. One L2 is worth more than three L1s.
