"""Tests for PatchApplier and ValidationEngine."""
from pathlib import Path
from backend.src.executor.applier import PatchApplier
from backend.src.executor.validation_engine import ValidationEngine
from backend.src.models.change_plan import ChangeType
from backend.src.models.patch_plan import FilePatch, PatchPlan


def test_patch_applier_create_modify_delete(tmp_path):
    # Setup initial file
    (tmp_path / "existing.py").write_text("initial = 1", encoding="utf-8")
    (tmp_path / "to_delete.py").write_text("delete_me", encoding="utf-8")

    plan = PatchPlan(
        story_id="STORY-APP",
        summary="Apply all 3 operation types",
        file_patches=[
            FilePatch(file_path="existing.py", change_type=ChangeType.MODIFY, content="initial = 2"),
            FilePatch(file_path="new_dir/created.py", change_type=ChangeType.CREATE, content="created = True"),
            FilePatch(file_path="to_delete.py", change_type=ChangeType.DELETE, content=None)
        ]
    )

    res = PatchApplier.apply_patch_plan(plan, tmp_path)
    assert res.success
    assert (tmp_path / "existing.py").read_text(encoding="utf-8") == "initial = 2"
    assert (tmp_path / "new_dir/created.py").read_text(encoding="utf-8") == "created = True"
    assert not (tmp_path / "to_delete.py").exists()


def test_patch_applier_traversal_rejection(tmp_path):
    plan = PatchPlan(
        story_id="STORY-TRAV",
        summary="Attack patch",
        file_patches=[
            FilePatch(file_path="../escape.py", change_type=ChangeType.CREATE, content="hacked")
        ]
    )
    res = PatchApplier.apply_patch_plan(plan, tmp_path)
    assert not res.success
    assert "Security rejection" in res.errors[0]


def test_validation_engine_python_execution(tmp_path):
    (tmp_path / "test_sample.py").write_text("def test_ok(): assert 1 == 1\n", encoding="utf-8")
    result = ValidationEngine.run_command("pytest test_sample.py", tmp_path, timeout_seconds=10)
    assert result.success
    assert result.return_code == 0
    assert "passed" in result.stdout.lower()


def test_validation_engine_timeout(tmp_path):
    (tmp_path / "slow.py").write_text("import time\ntime.sleep(5)\n", encoding="utf-8")
    result = ValidationEngine.run_command("python slow.py", tmp_path, timeout_seconds=1)
    assert not result.success
    assert result.timed_out

