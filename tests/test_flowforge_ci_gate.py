from scripts.check_flowforge_ci import ci_passed


COMMIT = "a" * 40
BRANCH = "feature/flowforge-architecture"


def run(run_id=1, **changes):
    result = {
        "id": run_id,
        "head_sha": COMMIT,
        "head_branch": BRANCH,
        "event": "push",
        "status": "completed",
        "conclusion": "success",
    }
    result.update(changes)
    return result


def approved(*runs):
    return ci_passed(
        {"workflow_runs": list(runs)},
        commit=COMMIT,
        branch=BRANCH,
    )


def test_accepts_successful_exact_commit():
    assert approved(run())


def test_rejects_different_commit_branch_and_pull_request():
    assert not approved(run(head_sha="b" * 40))
    assert not approved(run(head_branch="main"))
    assert not approved(run(event="pull_request"))


def test_newer_failed_or_pending_run_overrides_old_success():
    assert not approved(run(), run(2, conclusion="failure"))
    assert not approved(
        run(),
        run(2, status="in_progress", conclusion=None),
    )


def test_latest_rerun_attempt_must_pass():
    assert not approved(
        run(run_attempt=1),
        run(run_attempt=2, status="in_progress", conclusion=None),
    )


def test_rejects_missing_or_invalid_results():
    assert not approved()
    for payload in (None, [], {}, {"workflow_runs": None}):
        assert not ci_passed(payload, commit=COMMIT, branch=BRANCH)
