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

import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from wringer_drive.steps import ASK, CONFIRM, DONE, SHOW, STOPPED, Step

DRIVE_DIRNAME = Path(".wringer") / "drive"
PRD_FILENAME = "prd.md"


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


def run_command(repo: Path, argv: list[str]) -> subprocess.CompletedProcess:
    """One engine command, as a subprocess. Never `--send` unless told."""
    return subprocess.run(
        argv, cwd=repo, capture_output=True, text=True, check=False
    )


def final_step(repo: Path, board_path: Path) -> Step:
    return Step(
        kind=DONE,
        id="done",
        text=f"Open {board_path} to see what is done, what is proved, and "
        "what still needs you.",
        detail={"board": str(board_path)},
    )
