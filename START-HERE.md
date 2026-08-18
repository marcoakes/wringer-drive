# Start here — you are not an engineer and that is the point

You write down what you want, in ordinary English. A coding agent writes the
code. Wringer asks the questions, demands the proof, and refuses to hand over
work it cannot prove.

**Five steps. The first four are about ten minutes.**

---

## 1. Install it

Paste this into your coding agent — Claude Code, or whichever you use. It is
the whole instruction.

```text
Please install Wringer on this machine and set up its example for me. I am a product manager, not an engineer, so tell me what you are about to do before you do it, and tell me in plain language what happened afterwards.

Rules I am asking you to follow, and please tell me if any of them stop you:
  - Do not use sudo. Do not change any system setting.
  - Do not install anything except the tools named below and, if it is missing, the `uv` package manager they need.
  - Do not ask me for a password or an API key, and do not put one in a file or on a command line.
  - If a step fails, stop and show me the actual error. Do not work around it.

1. Check `git --version`, `uv --version` and `node --version` and tell me what you found. If `uv` is missing, install it for the current user only, following https://docs.astral.sh/uv/ .

2. Make a folder and clone all three repositories into it. They are public; no login is needed:
     git clone https://github.com/marcoakes/wringer.git
     git clone https://github.com/marcoakes/wringer-board.git
     git clone https://github.com/marcoakes/wringer-drive.git

3. Install them from source. The third command matters most, and the three must be installed together or it will not work:
     uv tool install --editable ./wringer
     uv tool install --editable ./wringer-board
     uv tool install --editable ./wringer-drive --with-editable ./wringer --with-editable ./wringer-board
   If `wring`, `wringer-board` and `wringer-drive` are not on my PATH afterwards, run `uv tool update-shell` and tell me to open a new terminal.

4. Install the adapter that lets Wringer drive Claude Code as the coding agent:
     npm install -g @agentclientprotocol/claude-agent-acp
   Then confirm the command `claude-agent-acp` is on my PATH.

5. Set up the example, and show me everything it prints:
     cd wringer-drive/examples/pipeline
     sh setup.sh ~/wringer-example

6. Tell me what is now installed and where, and confirm nothing was published anywhere.
```

### Your key — do this yourself, not through the agent

Wringer calls a model to read your document, and that costs money, so it needs
an **Anthropic API key** (the `sk-ant-…` string from
[console.anthropic.com](https://console.anthropic.com) → API keys). Not your
Claude password. Not your Mac password. It is billed per token on the API
account, separately from any Claude subscription — the calls in this guide cost
pennies.

In **Terminal**, not in your agent:

```bash
security add-generic-password -s anthropic -a wringer -w
```

There is deliberately no value after `-w`. Your Mac prompts you and hides what
you type, so the key never reaches your shell history, your screen, or anything
your agent can read.

---

## 2. See it work once, on something that already works

The agent's step 5 built you a small real project. Open a **new** terminal
window — new, because the install may have changed your PATH — and:

```bash
export WRINGER_API_KEY="$(security find-generic-password -s anthropic -a wringer -w)"
```

```bash
export PATH="$HOME/wringer-example/project/.venv/bin:$PATH" && cd ~/wringer-example/project && wringer-drive run ../PRD.md --repo .
```

It will ask you about ten questions. Three answers you will need:

| it asks | you answer |
|---|---|
| which model endpoint | `https://api.anthropic.com/v1/chat/completions` |
| which model | `claude-opus-5` |
| which coding agent should do the building | `acp: claude-agent-acp` |

Everything else is a product question and you are the person who answers it.
Then **open `board.html`**. [What you are looking at](docs/ENDINGS.md) explains
the four ways this can end.

> ### ⚠️ Known gap: the build step may stall with nothing on screen
>
> On a field run on 2026-08-18 the run reached the build and then sat silent.
> Reproduced since: the coding agent could not **authenticate**, and neither it
> nor Wringer said so. Wringer hands a worker only `PATH`, `HOME` and `LANG`, and
> depending on how your Claude Code is signed in, that may not be enough.
>
> **If nothing has happened for a couple of minutes**, it has probably stalled
> rather than gone quiet. Press Ctrl+C — nothing is lost, and no source file of
> yours will have been touched. Then tell us, because we still do not know how
> many machines this affects.
>
> Wringer's own guard would eventually stop it, but not for **fifteen minutes**,
> which is far too long to sit looking at a blank screen.

---

## 3. Work out which of your own repositories it can help with

This is the step people skip, and it is the one that decides whether any of
this works for you. **Wringer proves things. If a repository has nothing that
can decide whether a change is any good, there is nothing to prove with.**

Go into one of your repositories and ask it:

```bash
wring doctor
```

Two lines matter:

```
✓ runnable checks       2 could be detected from package.json
! last verify           never run here, so nothing is known yet
```

**`runnable checks`** is the gate. If it says `none — this repository declares
no test or lint command`, stop: nothing here can prove anything yet, and
Wringer will tell you the same thing five minutes later having taken your
document first. Somebody has to add a test command before this repository is a
candidate. That is not a small ask and it is not one you can do for them.

To calibrate: of **37 repositories** surveyed on one real account, **30 failed
this line.** That is normal. The ones that pass tend to be the ones somebody
has been maintaining properly.

**`last verify`** tells you whether those checks were passing last time anyone
looked. Red is not a disaster — it usually means work is in progress — but a
repository whose suite is already red will not get you a clean answer.

### The third thing, which no command can tell you

For a requirement to be **proved** rather than merely built, some check has to
exist *already* that **fails today** because the thing you are asking for does
not exist yet.

Teams that write the check first — before the feature — get proof. Teams that
write the test alongside the code get "built, unproved", which Wringer reports
honestly and will not dress up. Both examples in this repository are set up the
first way, and their READMEs explain the convention in a paragraph you can hand
to an engineer.

---

## 4. Write your requirement

[**The template and the four rules are here.**](docs/WRITING-A-REQUIREMENT.md)
It is a page long and it is the highest-leverage thing on this site, because a
vague document produces a confident specification for the wrong thing.

The short version: **write prose, name no files, ask for one thing, and say
what done looks like from a person's point of view.** Two real examples are
included — both produced good specifications from real models, so they are
evidence rather than illustration.

---

## 5. Drive your own repository

```bash
wringer-drive run YOUR-PRD.md --repo /path/to/your/project
```

Same questions, same two decisions, same board at the end.

**Expect a refusal the first time.** Most repositories cannot prove most
requirements, and a run that says so is the product working rather than
failing. [The four endings and what to do about each](docs/ENDINGS.md).

---

## What this will not do

It does not write your code — your coding agent does, and Wringer never touches
a source file. It does not decide whether your requirements are the right ones;
a check that passes against a badly worded requirement proves the wrong thing
perfectly. It does not sandbox your agent: driving with one verb runs it with
the same access you have, and there is no way to change that from here yet.

And it will not tell you a thing is done when it cannot show you the check that
proves it failing first.
