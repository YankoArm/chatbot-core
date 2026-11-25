"""Check whether an exact commit passed the deployment CI workflow."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def ci_passed(payload: object, *, commit: str, branch: str) -> bool:
    if not isinstance(payload, dict):
        return False

    runs = payload.get("workflow_runs")
    if not isinstance(runs, list):
        return False

    matching = [
        run
        for run in runs
        if isinstance(run, dict)
        and run.get("head_sha") == commit
        and run.get("head_branch") == branch
        and run.get("event") == "push"
        and isinstance(run.get("id"), int)
        and isinstance(run.get("run_attempt", 1), int)
    ]
    if not matching:
        return False

    latest = max(
        matching,
        key=lambda run: (run["id"], run.get("run_attempt", 1)),
    )
    return (
        latest.get("status") == "completed"
        and latest.get("conclusion") == "success"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--repository", default="YankoArm/chatbot-core")
    args = parser.parse_args()

    if not re.fullmatch(r"[0-9a-f]{40}", args.commit):
        parser.error("--commit must be a full Git commit SHA")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repository):
        parser.error("--repository must have owner/repository format")

    query = urlencode({
        "head_sha": args.commit,
        "branch": args.branch,
        "event": "push",
        "per_page": 100,
    })
    url = (
        f"https://api.github.com/repos/{args.repository}"
        f"/actions/workflows/flowforge-ci.yml/runs?{query}"
    )
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "FlowForge-Updater",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("FLOWFORGE_GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        with urlopen(Request(url, headers=headers), timeout=20) as response:
            payload = json.load(response)
    except Exception:
        # Avoid printing request headers or authentication material.
        print("Could not verify FlowForge CI on GitHub.", file=sys.stderr)
        return 1

    if not ci_passed(payload, commit=args.commit, branch=args.branch):
        print("Commit has no successful latest push run of FlowForge CI.")
        return 2

    print(f"FlowForge CI approved commit {args.commit}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
