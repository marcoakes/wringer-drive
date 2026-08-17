"""The verb: prose in, a board out — SPEC_DRIVE_V0 §2.

It composes the nineteen commands and invents no capability. Where a command
has `--json` it is a subprocess; where one does not, the package is imported as
a library and the permitted symbols are named in §3 ruling 1 rather than
reached for freely.

**What this file will not do**, because the whole point is that easy is not
unguarded:

- never auto-approve. There is no `--yes`, and the plan is rendered by DRIVE
  itself before the answer is taken. Ruling 2.
- never resolve a refusal. It renders them, in the board's words, and stops.
  Ruling 3.
- never write a judgement. A `human:` criterion is a person's, and nothing in
  any of the three packages writes one.
- never treat the approval at step 6 as authorising the delivery at step 9.
  Two acts, two answers. Ruling 2a.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from wringer_drive.steps import ASK, CONFIRM, DONE, SHOW, STOPPED, Step

DRIVE_DIRNAME = Path(".wringer") / "drive"
PRD_FILENAME = "prd.md"

# The engine verbs this package drives, and the refusal FAMILIES each can put
# in front of an operator. Declared here and checked against the source by
# `test_the_reachable_refusal_families_are_derived_from_what_DRIVE_DRIVES`, so
# a step added later either widens this set or fails.
#
# **Families, not values** (finding 10): `refusals.MAPPING` is keyed on
# `(family, value)` pairs deliberately, and 19 of its 45 pairs come from
# `attest`, `audit`, `health` and `fleet` — none of which appears in §2. A test
# over "every value" would demand sentences for stops this verb cannot reach.
ENGINE_VERBS: dict[str, tuple[str, ...]] = {
    "plan": (),
    "run": ("loop-ending",),
    "deliver": ("delivery-refusal",),
    # `wringer-board render` reads what the others wrote and refuses nothing.
    # Declared with an empty tuple rather than omitted, because the check is
    # that every verb DRIVEN is accounted for — silence would read as "not
    # driven", which is the state this exists to catch.
    "render": (),
}


class Stop(Exception):
    """The run stopped. Carries the step that says why, in the PM's language.

    Not called `Refused`: in this programme a `Refused` is the ENGINE's word
    with its own exit codes, and a surface inventing a second one with the same
    name is how two vocabularies start.
    """

    def __init__(self, step: Step, exit_code: int = 1) -> None:
        super().__init__(step.text)
        self.step = step
        self.exit_code = exit_code


@dataclass
class Session:
    """One run, and what it has emitted so far."""

    repo: Path
    steps: list[Step] = field(default_factory=list)

    def emit(self, step: Step) -> Step:
        self.steps.append(step)
        return step


# --- the three branches a stop can take (ruling 3) --------------------------


def stop_for(family: str, value: str, engine_words: str = "") -> Step:
    """A stop the board has a sentence for, or honestly does not.

    **Three branches, and the third is the one the drafted spec forgot**: a CLI
    refusal that carries no named value at all — `wring spec`'s "no `judge:`
    section", every `InterviewError` — is stderr prose with an exit code, and
    "unmapped" presupposes a key.
    """
    from wringer_board import refusals

    if not value:
        # Branch 3: no named value. The engine's own words, said to be its own.
        return Step(
            kind=STOPPED,
            id="stopped",
            text="This stopped, and here is exactly what the tool said.",
            engine_words=engine_words or "(the tool printed nothing)",
        )

    saying = refusals.say(family, value)
    if saying is None:
        # Branch 2: named, and this surface has no sentence for it. Ruling 17 —
        # a PM seeing an ugly string files a bug report; a PM seeing nothing
        # has been lied to.
        return Step(
            kind=STOPPED,
            id=f"stopped:{value}",
            text=f"This stopped for a reason this page has no wording for yet: {value}",
            engine_words=engine_words or None,
        )
    # Branch 1: mapped. The board's sentence and its unblocking question,
    # verbatim — this package writes neither.
    return Step(
        kind=STOPPED,
        id=f"stopped:{value}",
        text=saying.sentence,
        question=saying.question,
        engine_words=engine_words or None,
    )


# --- step 0: bring the PRD inside -------------------------------------------


def bring_prd_inside(session: Session, prd: Path) -> Path:
    """Copy the PRD into the repository, and say so.

    **Finding 16.** `spec.read_prd` refuses a PRD that resolves outside the
    repository, so a PM's obvious first move — pointing at `~/Desktop/PRD.md`
    — is refused today. Copying it is the smallest honest fix, and it is
    announced rather than done quietly: a verb that silently moves a person's
    files is a verb they cannot predict.
    """
    if not prd.is_file():
        raise Stop(
            Step(
                kind=STOPPED,
                id="stopped:no-prd",
                text=f"There is no file at {prd}. Point this at the document "
                "describing what you want built.",
            ),
            exit_code=2,
        )
    if not (session.repo / ".git").exists():
        raise Stop(
            Step(
                kind=STOPPED,
                id="stopped:not-a-repo",
                text=f"{session.repo} is not a git repository, and Wringer "
                "works on repositories. Ask an engineer to set one up, or "
                "point this at a project that already is one.",
            ),
            exit_code=2,
        )

    inside = session.repo / DRIVE_DIRNAME / PRD_FILENAME
    inside.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(prd, inside)
    session.emit(
        Step(
            kind=SHOW,
            id="prd-copied",
            text=f"I copied your document into the project, at "
            f"{inside.relative_to(session.repo)}, because the tool only reads "
            "files inside it. Your original is untouched.",
        )
    )
    return inside


# --- step 4: the interview --------------------------------------------------


def questions_to_ask(repo: Path) -> list[Step]:
    """One ASK per unanswered required question, in the spec's own words.

    The text is the drafter's question verbatim. This package does not rewrite
    a question to sound friendlier: the drafter asked it because it could not
    answer it, and softening it is how a PM answers a different question from
    the one that was asked.
    """
    from wringer_board import interview

    return [
        Step(
            kind=ASK,
            id=f"question:{q.id}",
            text=q.question,
            detail={"question_id": q.id},
        )
        for q in interview.unanswered(repo)
    ]


def record_answer(repo: Path, question_id: str, text: str) -> None:
    """Write one answer, through the board's own writer.

    Never a second implementation: `interview.answer` is what a person's hand
    edit is byte-compared against, and a copy here would be a second thing to
    keep in step.
    """
    from wringer_board import interview

    try:
        interview.answer(repo, question_id, text)
    except interview.InterviewError as exc:
        raise Stop(stop_for("", "", engine_words=str(exc)), exc.exit_code) from exc


# --- steps 5 and 6: the plan, then the approval -----------------------------


def plan_step(repo: Path) -> Step:
    """The plain-language plan, verbatim from the board."""
    from wringer_board import interview

    try:
        text = interview.plan(repo)
    except interview.InterviewError as exc:
        raise Stop(stop_for("", "", engine_words=str(exc)), exc.exit_code) from exc
    return Step(kind=SHOW, id="plan", text=text)


def approval_step() -> Step:
    """The one question the whole interlock rests on.

    **DRIVE renders the plan and takes the answer ITSELF** (ruling 2). It does
    not subprocess `wringer-board approve`: that verb takes the CALLER's word
    that a plan was shown, so a subprocess with a captured stdout would print
    the plan into a pipe and nobody would have read anything. Composition would
    launder the interlock SPEC_BOARD §5 ruling 20 exists to protect.
    """
    return Step(
        kind=CONFIRM,
        id="approve",
        text="That is what will be built, and how each piece will be proved.",
        question="Is that what you meant? Nothing is built until you say yes.",
        refusing_means="nothing is built, nothing is changed, and the plan "
        "stays where you can edit the requirements and try again.",
    )


def approve(repo: Path, *, answered_yes: bool) -> None:
    """Write `approved: true` — only on a yes, only after the plan was shown."""
    from wringer_board import interview

    if not answered_yes:
        raise Stop(
            Step(
                kind=STOPPED,
                id="stopped:not-approved",
                text="Nothing was built, because you did not approve the plan. "
                "Nothing in the project changed.",
            ),
            exit_code=0,
        )
    try:
        interview.approve(repo, read_the_plan=True)
    except interview.InterviewError as exc:
        if exc.exit_code == 0:
            return                     # already approved; not an error
        raise Stop(stop_for("", "", engine_words=str(exc)), exc.exit_code) from exc


# --- step 9's second authorisation (ruling 2a) ------------------------------


def delivery_step() -> Step:
    """**A SECOND authorisation, and approving the plan did not give it.**

    Steps 3 and 9 need `--send`, which is the typed flag that lets Wringer
    contact a model or write git history — and SPEC_GRAPH ruling 5's reason is
    that *a file is not a typed flag*. A verb that passed `--send` on the
    strength of a yes given at step 6 would be a file-driven authorisation
    wearing a flag.
    """
    return Step(
        kind=CONFIRM,
        id="deliver",
        text="The work is finished and the evidence is on the board.",
        question="Shall I hand this over — create the branch and open the "
        "merge request?",
        refusing_means="nothing is sent anywhere. The work and its evidence "
        "stay on this machine and you can hand it over later.",
    )


def engine(verb: str) -> str:
    """The `wring` this process should drive.

    **Beside `sys.executable` first, PATH second.** A DRIVE installed in a
    virtualenv is driving the engine installed in that same virtualenv; taking
    PATH's `wring` would silently drive a DIFFERENT install, which is the
    stale-`wring` defect this programme has already shipped once.
    """
    beside = Path(sys.executable).parent / verb
    return str(beside) if beside.is_file() else verb


def run_command(repo: Path, argv: list[str], env: dict | None = None
                ) -> subprocess.CompletedProcess:
    """One engine command, as a subprocess. Never `--send` unless told."""
    return subprocess.run(
        argv, cwd=repo, capture_output=True, text=True, check=False, env=env
    )


def _json_or_stop(done: subprocess.CompletedProcess, *, allow: tuple[int, ...]
                  ) -> dict:
    """The one JSON object a `--json` verb printed, or a stop carrying its words.

    `allow` is the exit codes whose stdout is still meant to be read — a loop
    that ends red exits non-zero and has said something worth rendering, and
    treating that as a crash would throw the engine's own account away.
    """
    if done.returncode not in allow:
        raise Stop(stop_for("", "", engine_words=(done.stderr or done.stdout).strip()),
                   done.returncode or 1)
    line = (done.stdout or "").strip().splitlines()
    try:
        return json.loads(line[-1]) if line else {}
    except json.JSONDecodeError:
        # It exited as expected and printed something that is not the object
        # this asked for. That is the engine's words, verbatim — never a
        # sentence written here about what it might have meant.
        raise Stop(stop_for("", "", engine_words=(done.stdout or "").strip()),
                   done.returncode or 1) from None


# --- step 7: install the approved gates (SPEC_DRIVE_V0 §3a) ------------------


def gate_proposal(repo: Path) -> dict:
    """What `wring plan` would like `.wringer.yaml` to have, as its own JSON.

    Read through `--json` rather than the prose report, because ruling 1
    forbids re-implementing an engine format and the report is a format.
    """
    return _json_or_stop(
        run_command(repo, [engine("wring"), "plan", "--json"]), allow=(0,)
    )


def gate_diff_step(proposal: dict) -> Step | None:
    """The diff itself, verbatim, or None when there is nothing to install.

    **None is not "nothing happened"** — it is the case where every proposed
    gate is already declared, and the caller says so rather than asking a
    person to approve an empty change. A yes to nothing is not consent.
    """
    diff = proposal.get("gate_diff") or ""
    if not diff.strip():
        return None
    return Step(
        kind=SHOW,
        id="gate-diff",
        text="Before anything is built, this adds the checks that will prove "
        "the work. This is the exact change to the project's settings:",
        engine_words=diff,
        detail={"gates": list(proposal.get("gates_proposed") or ())},
    )


def gate_approval_step(proposal: dict) -> Step:
    """The second interlock §3a rests on, asked after the diff was rendered."""
    names = ", ".join(proposal.get("gates_proposed") or ()) or "no new checks"
    return Step(
        kind=CONFIRM,
        id="install-gates",
        text=f"That change adds: {names}.",
        question="Shall I add those checks to the project?",
        refusing_means="the project's settings are left exactly as they are, "
        "and nothing is built.",
    )


def install_gates(repo: Path, proposal: dict, *, answered_yes: bool) -> bool:
    """Apply the rendered diff, and only it. §3a's four conditions.

    **`git apply`, not a writer of this package's own.** The diff `wring plan`
    printed IS the hand edit — `spec.gate_diff`'s own docstring says the `a/`
    and `b/` prefixes are there so `git apply` accepts it as-is. Applying it
    moves exactly the bytes the person read; a YAML round-trip here would
    reformat the file, drop every comment, and make byte-equality a fiction.

    Returns whether anything was installed.
    """
    diff = proposal.get("gate_diff") or ""
    if not diff.strip():
        return False
    if not answered_yes:
        raise Stop(
            Step(
                kind=STOPPED,
                id="stopped:gates-declined",
                text="Nothing was built, because the checks that would prove "
                "the work were not added. Nothing in the project changed.",
            ),
            exit_code=0,
        )
    done = subprocess.run(
        ["git", "apply", "--whitespace=nowarn", "-"],
        cwd=repo, input=diff, capture_output=True, text=True, check=False,
    )
    if done.returncode != 0:
        raise Stop(stop_for("", "", engine_words=(done.stderr or "").strip()),
                   done.returncode)
    return True


# --- step 8: the build loop -------------------------------------------------


def build_steps(repo: Path) -> list[Step]:
    """Run the loop, and say how it ended in the board's words.

    **Progress reaches the operator as steps, never as a bar** (§4): a
    percentage nothing measures is a number this package would be inventing,
    and inventing numbers is the whole thing it exists not to do.

    The ending is rendered through `refusals.say(LOOP_ENDING, ...)`, so an
    `environment` stop is a card like any other. F6's tiers are the ENGINE's
    to decide and this never widens one: it renders the reason it was given.
    """
    started = Step(
        kind=SHOW,
        id="building",
        text="Building now. This runs your project's own checks, hands each "
        "failure to your coding agent, and runs them again — for as many "
        "attempts as the project allows.",
    )
    outcome = _json_or_stop(
        run_command(repo, [engine("wring"), "run", "--json"]), allow=(0, 1)
    )
    reason = str(outcome.get("reason") or "")
    from wringer_board import refusals

    ending = stop_for(refusals.LOOP_ENDING, reason)
    return [
        started,
        Step(
            kind=SHOW if outcome.get("status") == "converged" else STOPPED,
            id=f"build:{reason or 'unknown'}",
            text=ending.text,
            question=ending.question,
            engine_words=ending.engine_words,
            detail={"iterations": outcome.get("iterations"),
                    "loop": outcome.get("loop_dir")},
        ),
    ]


def latest_refusal_step(repo: Path, engine_words: str) -> Step:
    """The engine's refusal, in the board's words — ruling 3's three branches.

    The record is the ONLY place the "which no" lives: `wring deliver` exits
    with a code and prints prose, and 23 different refusals share that code.
    `deliver.record_refusal` writes the name; `read.latest_refusal` finds it;
    `refusals.say` is the one place a sentence for it may come from.

    **A missing or unreadable record is branch 3, not a guess.** If the record
    cannot be read there is no named value, and inventing one from the prose
    would be this package deciding what the engine meant.
    """
    from wringer_board import read, refusals

    record = read.latest_refusal(repo)
    if record is None:
        return stop_for("", "", engine_words=engine_words)
    try:
        payload = json.loads(record.read_text(encoding="utf-8"))
        reason = str(payload["reason"])
    except (OSError, ValueError, KeyError):
        return stop_for("", "", engine_words=engine_words)
    return stop_for(refusals.DELIVERY_REFUSAL, reason, engine_words=engine_words)


def delivery_plan(repo: Path) -> dict:
    """What delivery WOULD do, without `--send`. Ruling 2a's first half.

    A refusal here is the common ending, not the exceptional one: the engine
    refuses a handover it cannot evidence, and that refusal is the product
    working. It is rendered, never resolved.
    """
    done = run_command(repo, [engine("wring"), "deliver", "--json"])
    if done.returncode != 0:
        raise Stop(
            latest_refusal_step(repo, (done.stderr or done.stdout).strip()),
            done.returncode,
        )
    return _json_or_stop(done, allow=(0,))


def deliver(repo: Path, *, answered_yes: bool) -> dict:
    """`--send`, and ONLY on a second yes given against the rendered board.

    Ruling 2a: the approval at step 6 was about what would be BUILT. This is
    about writing git history and opening a merge request, which is a
    different act about a different thing, and one yes may not cover both.
    """
    if not answered_yes:
        raise Stop(
            Step(
                kind=STOPPED,
                id="stopped:not-delivered",
                text="Nothing was sent anywhere. The work and its evidence "
                "stay on this machine, and you can hand it over later.",
            ),
            exit_code=0,
        )
    done = run_command(repo, [engine("wring"), "deliver", "--send", "--json"])
    if done.returncode != 0:
        raise Stop(
            latest_refusal_step(repo, (done.stderr or done.stdout).strip()),
            done.returncode,
        )
    return _json_or_stop(done, allow=(0,))


# --- step 10: the board -----------------------------------------------------


BOARD_FILENAME = "board.html"


def render_board(repo: Path) -> Path:
    """One page a person can read. The last thing the verb does, win or lose."""
    done = run_command(
        repo,
        [engine("wringer-board"), "render", str(repo), "-o", BOARD_FILENAME],
    )
    if done.returncode != 0:
        raise Stop(stop_for("", "", engine_words=(done.stderr or "").strip()),
                   done.returncode)
    return repo / BOARD_FILENAME


def board_step(board_path: Path) -> Step:
    return Step(
        kind=SHOW,
        id="board",
        text=f"The page showing what is done, what is proved, and what still "
        f"needs you is at {board_path.name}.",
        detail={"board": str(board_path)},
    )


def final_step(repo: Path, board_path: Path) -> Step:
    return Step(
        kind=DONE,
        id="done",
        text=f"Open {board_path} to see what is done, what is proved, and "
        "what still needs you.",
        detail={"board": str(board_path)},
    )
