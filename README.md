# wringer-drive

**One verb. A document in, a page out.**

```
wringer-drive run PRD.md
```

It takes what you wrote about what you want built, asks you the questions
nobody could answer for you, shows you a plan in plain language, and waits.
Nothing is built until you say yes.

## It is meant to be driven by your coding agent

You already have one — Wringer's [install page](https://github.com/marcoakes/wringer/blob/main/INSTALL.md)
is a prompt you paste into it. So this does not give you a new interface to
learn: `--emit json` produces one object per line for your agent to relay, and
your agent asks you the questions in the chat you are already in.

**Your agent is a transport, not a translator.** Every sentence it shows you
came from the engine or the board verbatim, never a summary. If nothing is
driving, the same steps appear at a terminal — the same words, laid out.

## What it will not do

- **There is no `--yes`.** The plan is rendered by this process, and the
  approval is answered by a person, and no flag or environment variable
  substitutes for that.
- **A stream with nobody behind it takes no default.** No answer means it
  stops and says so.
- **Approving the plan does not authorise the handover.** Two acts, two
  answers.
- **It never answers a `human:` criterion for you.** Nothing in any of the
  three packages writes a judgement.
- **It never resolves a refusal.** It shows you what the tool said and stops.

## State

**Steps 0 to 6 are built** — the document, the interview, the plan, the
approval. Steps 7 to 10 (install gates, build, deliver, render the board) are
not. The contract is
[SPEC_DRIVE_V0.md](https://github.com/marcoakes/wringer/blob/main/SPEC_DRIVE_V0.md),
independently reviewed before any of this was written — **NOT SOUND, 19
findings, all folded** — and its §8 is the list of what remains.

Filmed both ways: [docs/drive-2026-08-17.md](docs/drive-2026-08-17.md).

Apache-2.0, like the engine. No server, no network, no telemetry.
