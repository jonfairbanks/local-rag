from pathlib import Path
import re
import subprocess
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
        config = yaml.safe_load((ROOT / "docker-compose.yml").read_text())
        self.assertEqual(
            config["services"]["local-rag"]["ports"], ["127.0.0.1:8501:8501/tcp"]
        )


if __name__ == "__main__":
    unittest.main()
