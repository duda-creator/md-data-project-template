from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_TERMS = ("duck" + "db", "post" + "gres", "sql" + "server", "psy" + "copg")
REQUIRED_DIRECTORIES = (
    "data/1_raw",
    "data/2_interim",
    "data/3_processed",
    "data/4_profiling",
    "data/5_spec",
    "data/6_semantic",
    "data/7_reconciliation",
    "data-contracts",
    "notebooks",
    "references",
    "scripts",
    "src",
    "tests",
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class TemplateStructureTests(unittest.TestCase):
    def test_required_directories_have_placeholders(self) -> None:
        for relative_path in REQUIRED_DIRECTORIES:
            directory = ROOT / relative_path
            self.assertTrue(directory.is_dir(), relative_path)
            if relative_path in {"data-contracts", "tests", "src"}:
                continue
            self.assertTrue((directory / ".gitkeep").exists(), relative_path)

    def test_model_design_skills_have_required_artifacts(self) -> None:
        required_files = (
            ".github/skills/md-semantic-layer-design/SKILL.md",
            ".github/skills/md-semantic-layer-design/references/data_model_template.md",
            ".github/skills/md-semantic-layer-design/references/metric_dictionary_template.csv",
            ".github/skills/md-semantic-layer-design/references/model_decisions_template.md",
            ".github/skills/md-reconciliation-design/SKILL.md",
            ".github/skills/md-reconciliation-design/references/reconciliation_plan_template.md",
            ".github/skills/md-reconciliation-design/references/reconciliation_matrix_template.csv",
        )
        for relative_path in required_files:
            self.assertTrue((ROOT / relative_path).is_file(), relative_path)

        semantic_skill = (
            ROOT / ".github/skills/md-semantic-layer-design/SKILL.md"
        ).read_text(encoding="utf-8")
        reconciliation_skill = (
            ROOT / ".github/skills/md-reconciliation-design/SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("name: md-semantic-layer-design", semantic_skill)
        self.assertIn("references/metric-dictionary.csv", semantic_skill)
        self.assertIn("name: md-reconciliation-design", reconciliation_skill)
        self.assertIn(
            "data/7_reconciliation/reconciliation-matrix.csv", reconciliation_skill
        )

    def test_repository_content_has_no_platform_coupling(self) -> None:
        ignored_parts = {".git", ".venv", "__pycache__", ".pytest_cache"}
        for path in ROOT.rglob("*"):
            if not path.is_file() or ignored_parts.intersection(path.parts):
                continue
            if path.suffix.lower() not in {".md", ".py", ".toml", ".txt", ".csv", ""}:
                continue
            content = path.read_text(encoding="utf-8")
            for forbidden_term in FORBIDDEN_TERMS:
                self.assertNotIn(
                    forbidden_term, content.lower(), path.relative_to(ROOT)
                )

    def test_spec_builder_extends_approved_spec(self) -> None:
        builder = load_module(
            "template_spec_builder",
            ROOT / ".github/skills/md-table-spec-builder/scripts/build_table_spec.py",
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile = root / "data/4_profiling/2_interim/orders_profiling.csv"
            profile.parent.mkdir(parents=True)
            profile.write_text(
                "column,dtype,distinct_pct,missing_values\norder_id,object,1,0\n",
                encoding="utf-8",
            )
            output, added, skipped, _ = builder.build_spec(profile)
            self.assertEqual((added, skipped), (1, 0))
            content = output.read_text(encoding="utf-8").replace(",Draft", ",Approved")
            output.write_text(content, encoding="utf-8")
            _, added, skipped, _ = builder.build_spec(profile)
            self.assertEqual((added, skipped), (0, 1))

    @unittest.skipUnless(
        importlib.util.find_spec("pandas"), "profiling extra is not installed"
    )
    def test_profiler_writes_stage_aware_report(self) -> None:
        profiler = (
            ROOT / ".github/skills/md-source-extract-profiling/scripts/profile_file.py"
        )
        with tempfile.TemporaryDirectory(dir=ROOT / "data" / "2_interim") as directory:
            source = Path(directory) / "source.csv"
            source.write_text("item,value\na,1\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(profiler), str(source)],
                check=True,
                capture_output=True,
                text=True,
            )
            output_path = Path(result.stdout.strip())
            self.assertEqual(output_path.parent.name, "2_interim")
            self.assertEqual(output_path.parent.parent.name, "4_profiling")
            self.assertTrue(output_path.exists())
            output_path.unlink()


if __name__ == "__main__":
    unittest.main()
