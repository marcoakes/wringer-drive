"""DRIVE — SPEC_DRIVE_V0's four invariant tests, in their CORRECTED form.

The drafted versions were wrong in ways the refute review caught: test 1's
allow-set was short by five files and would have failed a *correct* build,
test 2 pinned something already false of the chain, test 3 asked for "every
value" over a mapping keyed on pairs with 19 of 45 unreachable, and test 4's
third clause had no hand edit to compare against.

The fifth thing here is the one that makes the transport decision safe:
**every PM-facing sentence came from the engine or the board, verbatim.**
"""

from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path

import pytest

from wringer_drive import run as run_module
from wringer_drive import steps as steps_module
from wringer_drive.__main__ import build_parser, main

SRC = Path(steps_module.__file__).parent


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """A real git repository with a spec the ENGINE rendered.

    Never a hand-typed fixture. Two live defects in this programme came from
    fixtures written on the same side of the seam as their reader, and the
    third would have been this one.
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
        # `brief` is a PATH `wring plan` writes to, not prose. The derived
        # allow-set caught this: prose here made the chain write a file
        # literally called "Build it" at the repository root.
        tasks=(
            spec.Task(id="build", brief="briefs/build.md", objective="It exports."),
        ),
        path="wringer.spec.yaml",
    )
    (repo / "wringer.spec.yaml").write_text(spec.render(drafted), encoding="utf-8")
    # **A project with the sections the CHAIN needs, not just the ones `wring
    # init` writes.** Steps 3, 8 and 9 each hard-refuse without `judge:`,
    # `run:` and `deliver:` — which is finding 3, and the reason §3a exists.
    # A fixture missing them tests a repository no operator could drive.
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
    """Deliberately OUTSIDE the repository — a PM's obvious first move."""
    path = tmp_path / "PRD.md"
    path.write_text("We need the weekly report as a CSV.\n", encoding="utf-8")
    return path


# --- INVARIANT 2: approval-stop --------------------------------------------


def test_there_is_no_flag_that_answers_the_approval():
    """**Ruling 2, structurally.** There is no `--yes`, and this reads the
    real parser rather than trusting that nobody added one."""
    parser = build_parser()
    flags = list(
        s for a in parser._actions for s in a.option_strings
    )
    for action in parser._actions:
        choices = getattr(action, "choices", None)
        if not hasattr(choices, "values"):
            continue
        for sub in choices.values():
            flags += [s for a in sub._actions for s in a.option_strings]
    assert "--emit" in flags, "the parser was not introspected at all"
    banned = ("--yes", "-y", "--auto", "--non-interactive", "--force", "--approve")
    for flag in banned:
        assert flag not in flags, f"{flag} answers an approval a person must give"

    # And no environment variable does either. Structural, with `ast`, for the
    # reason a text scan already failed once here: the module docstring says
    # "no flag or environment variable answers it", which a substring match
    # reads as the defect it is describing. A comment that cannot spell the
    # thing it explains is no use.
    reads = []
    for path in sorted(SRC.glob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Attribute) and node.attr in ("environ", "getenv"):
                reads.append(f"{path.name}:{node.lineno}")
            if isinstance(node, ast.Name) and node.id in ("environ", "getenv"):
                reads.append(f"{path.name}:{node.lineno}")
    assert reads == [], (
        f"DRIVE reads the environment at {reads}; an approval an environment "
        f"variable can give is not an approval"
    )


def test_a_stream_with_nobody_behind_it_STOPS_rather_than_defaulting(
    project, tmp_path, capsys
):
    """**A default here would be an approval nobody gave.**

    Piped stdin with nothing on it is the shape a CI job or a careless script
    has, and it must stop rather than pick a value.
    """
    import io
    import sys

    document = prd(tmp_path)
    original = sys.stdin
    sys.stdin = io.StringIO("")          # EOF immediately
    try:
        code = main(["run", str(document), "--repo", str(project)])
    finally:
        sys.stdin = original
    assert code == 2
    assert "nobody on the other end" in capsys.readouterr().err
    # And nothing was approved.
    assert "approved: false" in (project / "wringer.spec.yaml").read_text()


def test_a_no_at_the_plan_builds_nothing_and_changes_nothing(project, tmp_path, capsys):
    import io
    import sys

    document = prd(tmp_path)
    sys.stdin = io.StringIO("The ones on screen.\nno\n")
    try:
        code = main(["run", str(document), "--repo", str(project)])
    finally:
        sys.stdin = sys.__stdin__
    assert code == 0, "declining is not an error"
    out = capsys.readouterr()
    assert "did not approve" in (out.out + out.err)
    after = (project / "wringer.spec.yaml").read_text(encoding="utf-8")
    assert "approved: false" in after
    # The ANSWER was written — answering and approving are different acts.
    assert "The ones on screen." in after


def test_a_yes_approves_only_after_the_plan_was_rendered(project, tmp_path, capsys):
    import io
    import sys

    document = prd(tmp_path)
    sys.stdin = io.StringIO("The ones on screen.\nyes\n")
    try:
        main(["run", str(document), "--repo", str(project)])
    finally:
        sys.stdin = sys.__stdin__
    out = capsys.readouterr().out
    assert "HOW EACH PIECE WILL BE PROVED" in out
    assert out.index("HOW EACH PIECE") < out.index("Is that what you meant?")
    assert "approved: true" in (project / "wringer.spec.yaml").read_text()


def test_the_run_ends_at_a_refusal_rendered_in_the_boards_words(
    project, tmp_path, capsys
):
    """**The whole chain, and the ending it really has.**

    This fixture has no remote, so `wring deliver` refuses. That refusal is
    the product working, and what this pins is that a PM reads the BOARD's
    sentence for it rather than an exit code — through the record, which is
    the only place the name of the "which no" exists.
    """
    import io
    import sys

    from wringer_board import refusals

    document = prd(tmp_path)
    sys.stdin = io.StringIO("The ones on screen.\nyes\n")
    try:
        code = main(["run", str(document), "--repo", str(project)])
    finally:
        sys.stdin = sys.__stdin__
    assert code != 0, "a refused handover is not a success"

    saying = refusals.say(refusals.DELIVERY_REFUSAL, "default_branch_unknown")
    shown = capsys.readouterr()
    assert saying.sentence in (shown.out + shown.err), (
        "the refusal did not reach the operator in the board's words"
    )
    # And the board was still rendered — the page is how a person finds out
    # why, so a refusal may not cost them it.
    assert (project / "board.html").is_file()


# --- INVARIANT 1: no-file-edited, with the set DERIVED ----------------------


def test_it_writes_only_what_the_chain_is_entitled_to_write(project, tmp_path):
    """**CORRECTED, finding 5.** The drafted allow-set was short by five files
    and would have failed a correct build. It is derived from the commands'
    own filename constants, never typed out."""
    import io
    import sys

    spec = pytest.importorskip("wringer.spec")
    config = pytest.importorskip("wringer.config")

    entitled = {
        spec.SPEC_FILENAME,
        config.CONFIG_FILENAME,
        ".wringer",           # the bundle root, including drive's own output
        ".git",
        ".gitignore",         # `wring init`
        "briefs",             # `wring plan`, one brief per task
        run_module.BOARD_FILENAME,   # step 10, and DERIVED rather than typed
    }
    for attr in ("GATESPEC_FILENAME", "TASKS_FILENAME", "RUBRIC_FILENAME"):
        value = getattr(spec, attr, None)
        if value:
            entitled.add(value)

    before = {p.name for p in project.iterdir()}
    document = prd(tmp_path)
    sys.stdin = io.StringIO("The ones on screen.\nyes\n")
    try:
        main(["run", str(document), "--repo", str(project)])
    finally:
        sys.stdin = sys.__stdin__

    after = {p.name for p in project.iterdir()}
    new = after - before
    assert new <= entitled, (
        f"wrote files nothing entitles it to: {sorted(new - entitled)}"
    )


def test_the_prd_is_copied_inside_and_the_original_is_untouched(project, tmp_path):
    """Finding 16: `spec.read_prd` refuses a PRD outside the repository, so a
    PM pointing at their Desktop is refused today."""
    document = prd(tmp_path)
    original = document.read_text(encoding="utf-8")
    session = run_module.Session(repo=project)

    inside = run_module.bring_prd_inside(session, document)

    assert inside.is_file()
    assert inside.read_text(encoding="utf-8") == original
    assert document.read_text(encoding="utf-8") == original
    assert project in inside.parents
    # And it SAYS it did, rather than moving a person's files quietly.
    assert "copied your document" in session.steps[-1].text


def test_a_target_that_is_not_a_git_repository_stops_in_plain_language(tmp_path):
    session = run_module.Session(repo=tmp_path)
    with pytest.raises(run_module.Stop) as stopped:
        run_module.bring_prd_inside(session, prd(tmp_path))
    assert "not a git repository" in stopped.value.step.text
    assert "engineer" in stopped.value.step.text


# --- INVARIANT 3: refusal-surface, three branches ---------------------------


def test_a_mapped_refusal_renders_the_boards_sentence_and_its_question():
    from wringer_board import refusals

    step = run_module.stop_for(refusals.DELIVERY_REFUSAL, "gates_did_not_pass")
    saying = refusals.say(refusals.DELIVERY_REFUSAL, "gates_did_not_pass")
    assert step.text == saying.sentence
    assert step.question == saying.question


def test_a_named_value_with_no_sentence_renders_UNTRANSLATED():
    from wringer_board import refusals

    step = run_module.stop_for(
        refusals.DELIVERY_REFUSAL, "a-24th-nobody-mapped",
        engine_words="the tool said this",
    )
    assert "a-24th-nobody-mapped" in step.text
    assert step.engine_words == "the tool said this"


def test_a_refusal_with_NO_named_value_renders_the_engines_words_verbatim():
    """**The third branch, which the drafted spec forgot** (finding 11). The
    stops DRIVE meets first are stderr prose with an exit code and no key at
    all, so "unmapped" presupposes something they do not have."""
    step = run_module.stop_for(
        "", "", engine_words="no 'judge:' section in .wringer.yaml"
    )
    assert step.engine_words == "no 'judge:' section in .wringer.yaml"
    assert "exactly what the tool said" in step.text


def test_every_delivery_refusal_the_engine_can_emit_reaches_a_sentence():
    """Derived, both directions, from the engine's own closed tuple."""
    deliver = pytest.importorskip("wringer.deliver")
    from wringer_board import refusals

    for reason in deliver.REFUSAL_REASONS:
        step = run_module.stop_for(refusals.DELIVERY_REFUSAL, reason)
        assert step.question, reason
        assert "no wording for yet" not in step.text, reason


# --- THE TRANSPORT RULE: a transport, never a translator --------------------


def test_every_sentence_drive_emits_came_from_the_board_or_the_engine():
    """**The rule the whole transport decision rests on.**

    An agent relays what DRIVE emits. If DRIVE wrote its own sentences about
    criteria, refusals or gates, the agent would be relaying a SECOND surface's
    opinion — which SPEC_BOARD ruling 1 forbids, and which is the drift this
    programme keeps finding.

    Checked structurally: no string literal in `run.py`'s refusal paths may
    contain a refusal sentence of its own. The mapped branch assigns
    `saying.sentence` and `saying.question` and nothing else.
    """
    source = (SRC / "run.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    mapped = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "stop_for"
    )
    # The MAPPED branch — the last return — must take its PM-facing sentence
    # and question from the board's `Saying`, never from a literal here.
    # **Sorted by line, because `ast.walk` is breadth-first, not source
    # order** — the unsorted version picked branch 2's f-string and reported
    # the mapped branch as a literal, which is the guard being wrong about
    # the code rather than the code being wrong.
    returns = sorted(
        (n for n in ast.walk(mapped) if isinstance(n, ast.Return)),
        key=lambda n: n.lineno,
    )
    final = returns[-1]
    assigned = {kw.arg: kw.value for kw in final.value.keywords}

    sentence = assigned["text"]
    assert isinstance(sentence, ast.Attribute) and sentence.attr == "sentence", (
        "the mapped branch's `text` is not `saying.sentence` — DRIVE is "
        "writing its own sentence about a refusal, which makes an agent "
        "relaying it a second surface"
    )
    question = assigned["question"]
    assert isinstance(question, ast.Attribute) and question.attr == "question"

    # And no refusal-shaped prose anywhere in this package's own literals.
    for path in sorted(SRC.glob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                low = node.value.lower()
                assert "handover is being held" not in low, (
                    f"{path.name}:{node.lineno} writes a delivery-refusal "
                    f"sentence; that wording is the board's"
                )


def test_the_terminal_and_the_json_carry_the_SAME_text():
    """The fallback is a layout, not a second wording. That is the only reason
    the two front doors cannot drift into two products."""
    step = steps_module.Step(
        kind=steps_module.CONFIRM,
        id="x",
        text="The sentence.",
        question="The question?",
        refusing_means="nothing happens.",
    )
    rendered = step.as_terminal()
    payload = step.as_json()
    for value in (payload["text"], payload["question"], payload["refusing_means"]):
        assert value in rendered
    assert payload["schema_version"] == steps_module.SCHEMA_VERSION


def test_an_unknown_step_kind_is_refused_at_construction():
    with pytest.raises(ValueError, match="unknown step kind"):
        steps_module.Step(kind="whatever", id="x", text="y")


def test_the_json_mode_is_one_object_per_line(project, tmp_path, capsys):
    """What an agent reads. One line, one step, no framing to parse."""
    import io
    import sys

    document = prd(tmp_path)
    sys.stdin = io.StringIO("The ones on screen.\nyes\n")
    try:
        main(["run", str(document), "--repo", str(project), "--emit", "json"])
    finally:
        sys.stdin = sys.__stdin__

    lines = [row for row in capsys.readouterr().out.splitlines() if row.strip()]
    assert lines
    for line in lines:
        payload = json.loads(line)
        assert payload["schema_version"] == steps_module.SCHEMA_VERSION
        assert payload["kind"] in steps_module.KINDS
        assert payload["id"] and payload["text"]


# --- nothing writes a judgement, in any of the three packages ---------------


def test_nothing_in_drive_writes_a_judgement():
    """A `human:` criterion is a person's. Checked here as well as in the
    other two packages, because the DONE box requires all three."""
    for path in sorted(SRC.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        assert "judgements.yaml" not in text, path.name
        assert "judgement" not in text.lower() or "judgements.yaml" not in text
