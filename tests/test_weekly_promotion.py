from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "Static warning checks",
    "Tests and compile checks",
    "Build Docker Image",
)
HEAD = "a" * 40
PR = "https://github.com/example/local-rag/pull/1"


def check(name, run_id, status="completed", conclusion="success", app="github-actions"):
    return {
        "id": run_id,
        "name": name,
        "status": status,
        "conclusion": conclusion,
        "app": {"id": 15368 if app == "github-actions" else 123, "slug": app},
    }


@unittest.skipUnless(shutil.which("jq"), "The workflow requires jq")
class WeeklyPromotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        workflow = yaml.safe_load(
            (ROOT / ".github/workflows/weekly-develop-to-main.yml").read_text()
        )
        cls.script = next(
            step["run"]
            for step in workflow["jobs"]["promote"]["steps"]
            if step.get("name") == "Wait for Checks and Merge the Release"
        )

    def successes(self):
        return [check(name, i) for i, name in enumerate(REQUIRED, start=1)]

    def run_promotion(self, checks, head=HEAD):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = root / "fixture.json"
            fixture.write_text(json.dumps({"checks": checks, "head": head}))
            calls = root / "calls.jsonl"
            gh = root / "gh"
            gh.write_text(f"#!{sys.executable}\n" + """
import json, os, sys
from pathlib import Path
args = sys.argv[1:]
with Path(os.environ["MOCK_CALLS"]).open("a") as output:
    output.write(json.dumps(args) + "\\n")
data = json.loads(Path(os.environ["MOCK_FIXTURE"]).read_text())
if args[:2] == ["pr", "view"]:
    field = args[args.index("--json") + 1]
    print({"headRefOid": data["head"], "state": "MERGED"}[field])
elif args[0] == "api":
    assert args[args.index("--jq") + 1] == ".check_runs[]"
    for run in data["checks"]:
        print(json.dumps(run))
elif args[:2] != ["pr", "merge"]:
    sys.exit("Unexpected gh invocation: " + repr(args))
""")
            gh.chmod(0o755)
            sleep = root / "sleep"
            # Stop at the first wait instead of running all 180 polling attempts.
            sleep.write_text("#!/bin/sh\nexit 99\n")
            sleep.chmod(0o755)
            result = subprocess.run(
                ["/bin/bash", "-eo", "pipefail", "-c", self.script],
                env={
                    **os.environ,
                    "PATH": f"{root}:{os.environ['PATH']}",
                    "GH_REPO": "example/local-rag",
                    "PR_URL": PR,
                    "HEAD_SHA": HEAD,
                    "MOCK_FIXTURE": str(fixture),
                    "MOCK_CALLS": str(calls),
                },
                capture_output=True,
                text=True,
                timeout=10,
            )
            recorded = [json.loads(line) for line in calls.read_text().splitlines()]
            merges = [args for args in recorded if args[:2] == ["pr", "merge"]]
            return result, merges

    def assert_promotes(self, checks):
        result, merges = self.run_promotion(checks)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(
            merges,
            [["pr", "merge", PR, "--merge", "--auto", "--match-head-commit", HEAD]],
        )

    def assert_blocked(self, checks, *, waiting):
        result, merges = self.run_promotion(checks)
        self.assertEqual(merges, [], result.stdout + result.stderr)
        self.assertEqual(result.returncode, 99 if waiting else 1, result.stderr)
        self.assertIn(
            "Waiting for checks" if waiting else "Release checks failed",
            result.stdout + result.stderr,
        )

    def test_successful_required_checks_merge_the_exact_head(self):
        self.assert_promotes(self.successes())

    def test_running_promotion_does_not_block_itself(self):
        self.assert_promotes(
            self.successes()
            + [check("Promote Develop to Main", 10, "in_progress", None)]
        )

    def test_unrelated_failures_and_pending_checks_do_not_block(self):
        self.assert_promotes(
            self.successes()
            + [
                check("Optional analysis", 10, conclusion="failure"),
                check("Optional review", 11, "queued", None),
            ]
        )

    def test_missing_pending_and_skipped_required_checks_wait(self):
        for name in REQUIRED:
            for status, conclusion in (
                (None, None),
                ("queued", None),
                ("in_progress", None),
                ("completed", "skipped"),
            ):
                with self.subTest(name=name, status=status, conclusion=conclusion):
                    checks = [run for run in self.successes() if run["name"] != name]
                    if status is not None:
                        checks.append(check(name, 20, status, conclusion))
                    self.assert_blocked(checks, waiting=True)

    def test_unsuccessful_required_checks_fail(self):
        for name in REQUIRED:
            for conclusion in (
                "failure",
                "cancelled",
                "timed_out",
                "action_required",
                "stale",
            ):
                with self.subTest(name=name, conclusion=conclusion):
                    checks = [run for run in self.successes() if run["name"] != name]
                    checks.append(check(name, 20, conclusion=conclusion))
                    self.assert_blocked(checks, waiting=False)

    def test_foreign_app_cannot_satisfy_required_check(self):
        checks = self.successes()
        checks[0]["app"] = {"id": 123, "slug": "third-party"}
        self.assert_blocked(checks, waiting=True)

    def test_foreign_app_failure_with_required_name_is_ignored(self):
        self.assert_promotes(
            self.successes()
            + [check(REQUIRED[0], 20, conclusion="failure", app="third-party")]
        )

    def test_newest_required_run_replaces_old_success(self):
        for status, conclusion, waiting in (
            ("in_progress", None, True),
            ("completed", "failure", False),
        ):
            with self.subTest(status=status):
                self.assert_blocked(
                    [check(REQUIRED[0], 20, status, conclusion)] + self.successes(),
                    waiting=waiting,
                )

    def test_newest_success_replaces_old_failure(self):
        self.assert_promotes(
            [check(REQUIRED[0], 0, conclusion="failure")] + self.successes()
        )

    def test_changed_head_blocks_promotion(self):
        result, merges = self.run_promotion(self.successes(), head="b" * 40)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(merges, [])
        self.assertIn("Develop changed during promotion", result.stderr)


if __name__ == "__main__":
    unittest.main()
