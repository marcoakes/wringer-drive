"""Guards on what this package SAYS about itself, and on the ordering it ships.

`wringer-drive/tests/` had no doc guards at all until 2026-08-18, and on that
day this package's own README claimed steps 7 to 10 were not built while the
code drove all four of them, the core's roadmap listed the whole cycle as
queued, and a public README claimed an independent review the spec's own state
table denies. **One fact, three documents, three different answers.**

The two doc guards below are split the way `wringer-board`'s are: the
cross-repository half lives in the DEPENDENT repository and reaches back,
because this package imports `wringer` and the core does not import this. That
is the structural answer to the failure `wringer/docs/MANUAL_CHECKS.md:723-744`
recorded — a correction that landed in one repository and never crossed the
boundary to the other.

Neither guard keeps a list of what is built. The first reads the verbs this
package really drives; the second reads the core's README on disk.
"""

from __future__ import annotations

import ast
import io
import re
import subprocess
import sys
from pathlib import Path

import pytest

from wringer_drive import run as run_module

REPO = Path(__file__).resolve().parent.parent
SRC = Path(run_module.__file__).parent


def flattened(text: str) -> str:
    """Whitespace and emphasis markers flattened.

    The core's `tests/test_docs.py:785` rule. Re-stated rather than imported
    because the core's test module is not part of its installed package, and
    it is not optional: every document here wraps its sentences, and a
    line-wise search across a wrapped sentence matches nothing and cannot
    fail.
    """
    return " ".join(text.replace("*", "").split())


def own_voice(text: str) -> str:
    """A document's own claims, with `>` quoted material removed."""
    return "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith(">")
    )


# --- what is built, DERIVED from what this package drives -------------------
#
# SPEC_DRIVE_V0 §2's late steps, each mapped to the thing in this package that
# IS that step. Never a hand-kept "built: yes" list — that is the drift these
# guards exist to refuse.
#
# `ENGINE_VERBS` is a safe source because it is itself derived and checked:
# `test_the_reachable_refusal_families_are_derived_from_what_DRIVE_DRIVES`
# parses `run.py` with `ast` and fails if the declared verbs are not the verbs
# actually shelled out to. So this reads a fact the suite already pins.
LATE_STEPS: dict[int, str] = {
    7: "install the approved gates",
    8: "build — the repair loop",
    9: "hand over — `wring deliver`",
    10: "render the board",
}


def steps_the_code_performs() -> set[int]:
    """Which of §2's late steps this package demonstrably performs."""
    built = set()
    if callable(getattr(run_module, "install_gates", None)):
        built.add(7)
    if "run" in run_module.ENGINE_VERBS:
        built.add(8)
    if "deliver" in run_module.ENGINE_VERBS:
        built.add(9)
    if "render" in run_module.ENGINE_VERBS:
        built.add(10)
    return built


NOT_BUILT = re.compile(
    r"\b(?:are|is)\s+not\b(?!\s+(?:yet\s+)?(?:the|a|an)\b)"
    r"|\bnot\s+(?:yet\s+)?built\b"
    r"|\bremains?\s+unbuilt\b"
    r"|\bstill\s+to\s+(?:be\s+)?(?:built|come)\b",
    re.I,
)
STEP_RANGE = re.compile(
    r"\bsteps?\s+(\d+)\s*(?:to|through|and|[-–—])\s*(\d+)", re.I
)
STEP_ONE = re.compile(r"\bstep\s+(\d+)\b", re.I)


def steps_claimed_unbuilt(text: str) -> dict[int, str]:
    """Step numbers a document says, in its own voice, are not built."""
    claimed: dict[int, str] = {}
    for sentence in re.split(r"(?<=[.!?])\s+", flattened(own_voice(text))):
        if not NOT_BUILT.search(sentence):
            continue
        numbers: set[int] = set()
        for low, high in STEP_RANGE.findall(sentence):
            numbers.update(range(int(low), int(high) + 1))
        numbers.update(int(n) for n in STEP_ONE.findall(sentence))
        for number in numbers:
            claimed.setdefault(number, sentence)
    return claimed


def test_the_readme_does_not_claim_unbuilt_what_the_code_drives():
    """**Red on the real defect, 2026-08-18.**

    `README.md:39-41` said *"Steps 7 to 10 (install gates, build, deliver,
    render the board) are not [built]"* while `ENGINE_VERBS` declares `run`,
    `deliver` and `render` — verbs the suite separately proves are really
    shelled out to — and `install_gates` is a function in `run.py` with three
    tests of its own.

    The fact is read off the code every time this runs. A step that is later
    REMOVED makes this guard permit the sentence again, which is the correct
    direction: the document may say what the code does, whichever way it
    moves.
    """
    built = steps_the_code_performs()
    assert built, (
        "no late step could be derived from the code at all, so this guard "
        "would pass while checking nothing — `ENGINE_VERBS` or "
        "`run.install_gates` moved"
    )

    readme = (REPO / "README.md").read_text(encoding="utf-8")
    claimed = steps_claimed_unbuilt(readme)
    contradicted = {n: s for n, s in claimed.items() if n in built}

    assert not contradicted, (
        "this package performs "
        + ", ".join(f"step {n} ({LATE_STEPS[n]})" for n in sorted(built))
        + " — and its own README says otherwise:\n"
        + "\n".join(f"  step {n}: {s}" for n, s in sorted(contradicted.items()))
    )


REVIEW_OVERCLAIM = re.compile(r"\bindependently\s+reviewed\b", re.I)


def test_the_readme_does_not_call_the_specs_review_independent():
    """**The worst class of contradiction a trust product can carry: a claim
    about verification itself.**

    `SPEC_DRIVE_V0.md`'s header records a review; its §11 state table says
    `independently reviewed | NO. Not begun`; and this README said
    *"independently reviewed"* in public — resolving the contradiction in the
    flattering direction.

    Ruled 2026-08-18 from §12's own text: the review was a same-day,
    one-agent refute pass by the window that then built to the spec — real,
    NOT SOUND, 19 findings, all folded — and *independent* is this house's
    word for a separate later review, which has not begun. The README may
    describe what the record shows and not a word more.

    Derived, not pinned: the core's §11 row is read at test time, so if a
    genuinely independent review ever runs and flips that row, this guard
    stops forbidding the word rather than having to be remembered.
    """
    spec = spec_drive_text()
    says_no = re.search(
        r"independently\s+reviewed\s*\|[^|\n]*\bNO\b", flattened(own_voice(spec)), re.I
    )
    assert says_no, (
        "SPEC_DRIVE_V0 §11 no longer carries an `independently reviewed | NO` "
        "row, so this guard would pass while checking nothing. If a real "
        "independent review ran, delete this guard and say so; if the row was "
        "merely reworded, re-derive the pattern"
    )

    readme = flattened(own_voice((REPO / "README.md").read_text(encoding="utf-8")))
    hit = REVIEW_OVERCLAIM.search(readme)
    assert hit is None, (
        "SPEC_DRIVE_V0 §11 says the spec has NOT been independently reviewed, "
        "and this public README claims it has: "
        f"…{readme[max(0, hit.start() - 70): hit.end() + 70]}…"
    )


# --- the cross-repository half ----------------------------------------------


def core_root() -> Path:
    """The CORE repository, found through the engine this package drives."""
    wringer = pytest.importorskip(
        "wringer.accept",
        reason="the core is not importable, so its README and SPEC_DRIVE_V0 "
        "cannot be located. Nothing else checks that the core's roadmap and "
        "this package agree about whether this package exists, and this is "
        "that gap being named",
    )
    return Path(wringer.__file__).resolve().parents[2]


def core_readme() -> str:
    path = core_root() / "README.md"
    if not path.is_file():
        pytest.skip(f"the core is importable but {path} is absent")
    return path.read_text(encoding="utf-8")


def spec_drive_text() -> str:
    path = core_root() / "SPEC_DRIVE_V0.md"
    if not path.is_file():
        pytest.skip(f"the core is importable but {path} is absent")
    return path.read_text(encoding="utf-8")


QUEUE_CLOSER = "Nothing above is claimed as existing"


def queued_rows(readme: str) -> list[str]:
    """The rows of the core README's "what is queued now" table.

    Located by its own closing sentence rather than by line number: the table
    is whatever `|`-rows stand between the last table header before that
    sentence and the sentence itself.
    """
    lines = readme.splitlines()
    closing = next(
        (i for i, line in enumerate(lines) if QUEUE_CLOSER in line), None
    )
    assert closing is not None, (
        f"the core README no longer contains {QUEUE_CLOSER!r}, which is how "
        f"this guard finds the queue. It moved — re-derive the anchor rather "
        f"than deleting this assertion"
    )
    rows = []
    for line in reversed(lines[:closing]):
        stripped = line.strip()
        if not stripped:
            if rows:
                break
            continue
        if not stripped.startswith("|"):
            break
        rows.append(stripped)
    return list(reversed(rows))


def test_the_core_roadmap_does_not_deny_this_package_exists():
    """**Red on the real defect, 2026-08-18.**

    `wringer/README.md:711-724` listed *"The drive cycle — the operating gap —
    one verb from a prose file to a rendered board"* under **what is queued
    now**, closed by *"Nothing above is claimed as existing."* This package is
    that cycle, it is built through step 10, and its wall clock is measured in
    `docs/pm-mode-2026-08-17.md`.

    The other direction of the same fact as the README guard above, and it is
    here rather than in the core for the same reason the board's publication
    guard is in the board: the dependent repository can see both sides.
    """
    built = steps_the_code_performs()
    assert built, "nothing derivable from the code, so this checks nothing"

    rows = queued_rows(core_readme())
    assert rows, (
        "no table rows were found above the core README's queue closer, so "
        "this guard would pass while checking nothing"
    )

    denied = [row for row in rows if re.search(r"\bdrive\b", row, re.I)]
    assert not denied, (
        "the core README lists this package under what is QUEUED, closed by "
        f"{QUEUE_CLOSER!r} — while it drives "
        + ", ".join(f"step {n}" for n in sorted(built))
        + ":\n"
        + "\n".join(f"  {row}" for row in denied)
    )


def test_the_core_roadmap_TABLE_does_not_mark_this_cycle_queued():
    """**A thirteenth contradiction, found by reading rather than by a guard —
    which is exactly why it is now a guard.**

    `ROADMAP.md`'s cycle table had **The drive cycle** in a row whose state
    cell read `queued`, under a heading saying *"nothing in it is claimed as
    existing"*, on 2026-08-18. The README guard above could not see it: it
    reads the README's queue table and stops at the file boundary. Same
    class, one document over.

    Derived the same way: the state cell of any row naming this cycle may not
    say `queued` while the code performs the steps.
    """
    built = steps_the_code_performs()
    assert built, "nothing derivable from the code, so this checks nothing"

    path = core_root() / "ROADMAP.md"
    if not path.is_file():
        pytest.skip(f"the core is importable but {path} is absent")

    rows = [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip().startswith("|")
    ]
    assert rows, "no table rows in the core ROADMAP at all"

    named = [row for row in rows if re.search(r"\bdrive cycle\b", row, re.I)]
    assert named, (
        "the core ROADMAP no longer has a row naming the drive cycle, so this "
        "guard would pass while checking nothing. If the row was renamed, "
        "re-derive the pattern; if the table went, say so here"
    )

    queued = [
        row for row in named
        if re.search(r"\|\s*(?:queued|planned|not started)\s*\|?\s*$", row, re.I)
    ]
    assert not queued, (
        "the core ROADMAP marks this cycle queued while it drives "
        + ", ".join(f"step {n}" for n in sorted(built))
        + ":\n"
        + "\n".join(f"  {row}" for row in queued)
    )


# --- the board-path ordering, pinned on BOTH endings ------------------------


def recording_session(monkeypatch) -> list:
    """Capture the `Session` `main()` builds, so its ordered steps are readable.

    `session.steps` is the ordered record of everything emitted, including the
    final stop — which is the only place the two streams (`stdout` for steps,
    `stderr` for a non-zero stop) can be compared as one sequence.
    """
    made: list = []
    real = run_module.Session

    def build(**kwargs):
        session = real(**kwargs)
        made.append(session)
        return session

    monkeypatch.setattr(run_module, "Session", build)
    return made


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """The same real repository `test_drive.py`'s fixture builds.

    Duplicated rather than imported so this file stands alone; the shape is
    the engine's, written through `wringer.spec.render`, never hand-typed
    YAML.
    """
    spec = pytest.importorskip("wringer.spec")
    repo = tmp_path / "project"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    for key, value in (("user.email", "pm@e.invalid"), ("user.name", "PM"),
                       ("commit.gpgsign", "false")):
        subprocess.run(["git", "config", key, value], cwd=repo, check=True)
    drafted = spec.Spec(
        approved=False,
        title="Weekly report export",
        intent="A manager can export the weekly report as a CSV.",
        questions=(
            spec.Question(id="which-columns", question="Which columns?", required=True),
        ),
        criteria=(
            spec.Criterion(id="exports-csv", title="It exports a CSV", required=True),
        ),
        gates=(),
        tasks=(
            spec.Task(id="build", brief="briefs/build.md", objective="It exports."),
        ),
        path="wringer.spec.yaml",
    )
    (repo / "wringer.spec.yaml").write_text(spec.render(drafted), encoding="utf-8")
    (repo / ".wringer.yaml").write_text(
        'version: 1\n'
        'gates:\n'
        '  - id: unit\n'
        '    run: "true"\n'
        '\n'
        'judge:\n'
        '  endpoint: http://127.0.0.1:1/v1/chat/completions\n'
        '  model: none\n'
        '  rubric: wringer.rubric.yaml\n'
        '\n'
        'run:\n'
        '  worker: "true"\n'
        '  max_iterations: 1\n'
        '\n'
        'deliver:\n'
        '  branch: "wringer/{run}"\n',
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)
    return repo


def prd(tmp_path: Path) -> Path:
    path = tmp_path / "PRD.md"
    path.write_text("We need the weekly report as a CSV.\n", encoding="utf-8")
    return path


def drive(project: Path, tmp_path: Path, answers: str, monkeypatch) -> tuple[int, list]:
    from wringer_drive.__main__ import main

    made = recording_session(monkeypatch)
    sys.stdin = io.StringIO(answers)
    try:
        code = main(["run", str(prd(tmp_path)), "--repo", str(project)])
    finally:
        sys.stdin = sys.__stdin__
    assert made, "the session was never built"
    return code, made[0].steps


def test_a_refused_run_still_emits_the_board_AND_SAYS_THE_REFUSAL_LAST(
    project, tmp_path, capsys, monkeypatch
):
    """**Deliberate ordering, pinned so a tidy-up cannot reverse it.**

    This fixture has no remote, so `wring deliver` refuses — the common
    ending, and the product working. Two things must hold together and it is
    easy to break one while fixing the other:

    - the board is still rendered and still announced, because the page is
      how a person finds out WHY;
    - the refusal is the LAST thing said, because the refusal is the news. A
      run that ends on "your page is at board.html" reads as a success.
    """
    code, steps = drive(project, tmp_path, "The ones on screen.\nyes\n", monkeypatch)
    capsys.readouterr()

    assert code != 0, "a refused handover is not a success"
    ids = [step.id for step in steps]
    assert "board" in ids, f"a refused run never announced the board: {ids}"
    assert (project / run_module.BOARD_FILENAME).is_file()
    assert ids[-1].startswith("stopped"), (
        f"a refused run ended on {ids[-1]!r} rather than on the refusal; the "
        f"refusal is the news and it must be the last word: {ids}"
    )
    assert ids.index("board") < len(ids) - 1


def test_a_converged_run_emits_the_board_TOO_and_ends_on_the_page(
    project, tmp_path, capsys, monkeypatch
):
    """The other ending, and the reason the ordering is not an accident.

    **What is substituted, stated rather than hidden:** only the engine's
    delivery VERDICT. `delivery_plan` and `deliver` are replaced so the
    converged branch is reachable — this fixture cannot honestly converge,
    since nothing evidences its criterion and there is no remote to push to.
    Everything else is real, including `wringer-board render`, which writes
    the page this asserts exists.

    What is being pinned is DRIVE's ordering, not the engine's answer, and
    the engine's answer is exactly the input a test is entitled to choose.
    """
    monkeypatch.setattr(run_module, "delivery_plan", lambda repo: {"would": "send"})
    monkeypatch.setattr(
        run_module, "deliver", lambda repo, *, answered_yes: {"sent": answered_yes}
    )

    code, steps = drive(
        project, tmp_path, "The ones on screen.\nyes\nyes\n", monkeypatch
    )
    capsys.readouterr()

    assert code == 0, f"a converged run should exit 0, got {code}"
    ids = [step.id for step in steps]
    assert "board" in ids, f"a converged run never announced the board: {ids}"
    assert ids[-1] == "done", f"a converged run ended on {ids[-1]!r}: {ids}"
    assert (project / run_module.BOARD_FILENAME).is_file()


def test_both_endings_render_the_board_in_the_orchestrator_itself():
    """The structural half, and it is what stops a refactor from removing one
    branch while the other stays green.

    `__main__._run` renders the board on the refused branch (inside the
    `except run_module.Stop`) and on the converged one (after it). Both call
    sites are read out of the source with `ast`, so deleting either reddens
    this even if a live test happens not to reach that path.
    """
    source = (SRC / "__main__.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    run_fn = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "_run"
    )

    handlers = [n for n in ast.walk(run_fn) if isinstance(n, ast.ExceptHandler)]
    assert handlers, "`_run` no longer catches a Stop around delivery"

    def renders_board(node) -> bool:
        return any(
            isinstance(call, ast.Call)
            and getattr(call.func, "attr", None) == "render_board"
            for call in ast.walk(node)
        )

    inside = [h for h in handlers if renders_board(h)]
    assert inside, (
        "no `except Stop` handler in `_run` renders the board — a refused run "
        "would leave the person without the page that explains why"
    )
    for handler in inside:
        assert any(isinstance(n, ast.Raise) for n in ast.walk(handler)), (
            "the refusal-branch handler renders the board and then swallows "
            "the Stop; the refusal must still be the last word"
        )

    handler_lines = {
        line
        for h in inside
        for line in (getattr(n, "lineno", None) for n in ast.walk(h))
        if line is not None
    }
    outside = [
        call for call in ast.walk(run_fn)
        if isinstance(call, ast.Call)
        and getattr(call.func, "attr", None) == "render_board"
        and call.lineno not in handler_lines
    ]
    assert outside, (
        "the board is rendered only on the refused branch — a converged run "
        "would finish without a page"
    )
