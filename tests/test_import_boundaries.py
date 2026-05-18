import subprocess
import sys
import textwrap
import unittest


class ImportBoundaryTests(unittest.TestCase):
    def test_lightweight_modules_do_not_import_torch_at_module_load(self):
        script = textwrap.dedent(
            """
            import builtins

            original_import = builtins.__import__

            def guarded_import(name, *args, **kwargs):
                blocked = (
                    name == "torch"
                    or name.startswith("torch.")
                    or name == "llama_index.embeddings.huggingface"
                    or name.startswith("llama_index.embeddings.huggingface.")
                )
                if blocked:
                    raise AssertionError(f"unexpected eager import: {name}")
                return original_import(name, *args, **kwargs)

            builtins.__import__ = guarded_import

            import utils.rag_pipeline
            import components.tabs.github_repo
            import components.tabs.local_files
            """
        )

        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(
            result.returncode,
            0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
