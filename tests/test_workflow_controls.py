from pathlib import Path
import json
import os
import re
import subprocess
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]


class WorkflowControlsTests(unittest.TestCase):
    def test_actions_are_pinned_and_build_token_is_read_only(self):
        for path in (ROOT / ".github/workflows").glob("*.y*ml"):
            for action in re.findall(r"uses:\s*(\S+)", path.read_text()):
                self.assertRegex(action, r"^[\w-]+/[\w-]+@[0-9a-f]{40}$")
        workflow = yaml.safe_load((ROOT / ".github/workflows/main.yaml").read_text())
        self.assertEqual(
            workflow["jobs"]["docker"]["permissions"], {"contents": "read"}
        )
        self.assertEqual(
            workflow["jobs"]["version"]["permissions"], {"contents": "write"}
        )
        self.assertIn("github.event_name == 'push'", workflow["jobs"]["version"]["if"])
        for job in workflow["jobs"].values():
            for step in job["steps"]:
                if step.get("uses", "").startswith("actions/checkout@"):
                    self.assertFalse(step["with"]["persist-credentials"])

    def test_dependabot_auto_merge_is_patch_only_and_develop_only(self):
        workflow = yaml.safe_load(
            (ROOT / ".github/workflows/dependabot-auto-merge.yml").read_text()
        )
        job = workflow["jobs"]["enable-automerge"]
        self.assertIn("base.ref == 'develop'", job["if"])
        merge_step = next(
            step for step in job["steps"] if "--auto --squash" in step.get("run", "")
        )
        self.assertEqual(
            merge_step["if"],
            "steps.metadata.outputs.update-type == 'version-update:semver-patch'",
        )
        self.assertIn("--match-head-commit", merge_step["run"])
        self.assertFalse(
            any("checkout@" in step.get("uses", "") for step in job["steps"])
        )

    def test_release_tag_failure_is_reported_when_build_is_skipped(self):
        workflow = yaml.safe_load((ROOT / ".github/workflows/main.yaml").read_text())
        notification = workflow["jobs"]["notify"]
        self.assertEqual(notification["needs"], ["version", "docker"])
        expression = notification["steps"][0]["with"]["status"]
        self.assertEqual(
            expression,
            "${{ needs.version.result == 'failure' && 'failure' || needs.docker.result }}",
        )

    def test_issue_script_compiles_and_uses_injected_client(self):
        workflow = yaml.safe_load(
            (ROOT / ".github/workflows/issue-attachments.yaml").read_text()
        )
        script = workflow["jobs"]["remind"]["steps"][0]["with"]["script"]
        harness = """
const fs = require('node:fs');
const AsyncFunction = Object.getPrototypeOf(async function() {}).constructor;
const run = new AsyncFunction('github', 'context', fs.readFileSync(0, 'utf8'));
let count = 0;
const github = { rest: { issues: { createComment: async () => { count++; } } } };
const context = { repo: { owner: 'test', repo: 'test' }, issue: { number: 1 }, payload: { issue: { body: null } } };
(async () => {
  await run(github, context);
  if (count !== 1) throw new Error('Expected reminder');
  context.payload.issue.body = 'https://github.com/user-attachments/example';
  await run(github, context);
  if (count !== 1) throw new Error('Unexpected duplicate reminder');
})().catch(error => { console.error(error); process.exitCode = 1; });
"""
        result = subprocess.run(
            ["node", "-e", harness],
            input=script,
            text=True,
            capture_output=True,
            cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_browser_storage_message_contract(self):
        result = subprocess.run(
            ["node", "tests/test_browser_component.js"],
            text=True,
            capture_output=True,
            cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_compose_only_publishes_to_loopback(self):
        for name in (
            "docker-compose.yml",
            "docker-compose.yml-cpu",
            "docker-compose.yml-rocm",
        ):
            with self.subTest(name=name):
                config = yaml.safe_load((ROOT / name).read_text())
                self.assertEqual(
                    config["services"]["local-rag"]["ports"],
                    ["127.0.0.1:8501:8501/tcp"],
                )

    def test_native_builds_share_a_required_gate(self):
        jobs = yaml.safe_load((ROOT / ".github/workflows/main.yaml").read_text())[
            "jobs"
        ]
        build = jobs["build"]
        self.assertEqual(
            {
                (row["arch"], row["runner"])
                for row in build["strategy"]["matrix"]["include"]
            },
            {("amd64", "ubuntu-24.04"), ("arm64", "ubuntu-24.04-arm")},
        )
        self.assertEqual(jobs["docker"]["name"], "Build Docker Image")
        self.assertIn("build", jobs["docker"]["needs"])
        self.assertEqual(jobs["docker"]["if"], "always()")
        gate = jobs["docker"]["steps"][0]["run"]
        for status in ("success", "failure", "cancelled", "skipped"):
            result = subprocess.run(
                ["bash", "-c", gate], env={**os.environ, "BUILD_RESULT": status}
            )
            self.assertEqual(result.returncode == 0, status == "success")

    def test_pr_builds_do_not_publish_or_export_cache(self):
        jobs = yaml.safe_load((ROOT / ".github/workflows/main.yaml").read_text())[
            "jobs"
        ]
        for job in (jobs["build"], jobs["docker"]):
            for step in job["steps"]:
                config = step.get("with", {})
                if any(key in config for key in ("cache-to", "password", "outputs")):
                    self.assertEqual(step.get("if"), "github.event_name == 'push'")
        test_step = next(
            s
            for s in jobs["build"]["steps"]
            if s.get("with", {}).get("target") == "test"
        )
        self.assertIn("matrix.arch", test_step["with"]["cache-from"])
        self.assertNotIn("cache-to", test_step["with"])

    def test_manifest_uses_both_digests_and_expected_tags(self):
        jobs = yaml.safe_load((ROOT / ".github/workflows/main.yaml").read_text())[
            "jobs"
        ]
        step = jobs["docker"]["steps"][-1]
        self.assertEqual(step["if"], "github.event_name == 'push'")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "digests").mkdir()
            for arch, char in (("amd64", "a"), ("arm64", "b")):
                (root / "digests" / f"{arch}.digest").write_text(
                    f"sha256:{char * 64}\n"
                )
            docker = root / "docker"
            docker.write_text("""#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
if sys.argv[3] == "create":
    Path(os.environ["MOCK_OUTPUT"]).write_text(json.dumps(sys.argv[1:]))
elif sys.argv[3] == "inspect":
    print(json.dumps({"manifests": [{"platform": {"os": "linux", "architecture": arch}} for arch in ("amd64", "arm64")]}))
else:
    sys.exit(1)
""")
            docker.chmod(0o755)
            output = root / "arguments.json"
            env = {
                **os.environ,
                "PATH": f"{root}:{os.environ['PATH']}",
                "RUNNER_TEMP": str(root),
                "MOCK_OUTPUT": str(output),
                "IMAGE": "example/local-rag",
                "RELEASE_TAG": "v2.1.0",
            }
            for branch, tags in (
                ("develop", ["develop"]),
                ("main", ["v2.1.0", "latest"]),
            ):
                result = subprocess.run(
                    ["bash", "-eo", "pipefail", "-c", step["run"]],
                    env={**env, "GITHUB_REF_NAME": branch},
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                args = json.loads(output.read_text())
                actual_tags = [
                    args[i + 1] for i, arg in enumerate(args) if arg == "--tag"
                ]
                self.assertEqual(
                    actual_tags, [f"example/local-rag:{tag}" for tag in tags]
                )
                self.assertEqual(
                    args[-2:],
                    [f"example/local-rag@sha256:{char * 64}" for char in "ab"],
                )
            output.unlink()
            (root / "digests/arm64.digest").unlink()
            result = subprocess.run(
                ["bash", "-eo", "pipefail", "-c", step["run"]],
                env={**env, "GITHUB_REF_NAME": "develop"},
                capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
