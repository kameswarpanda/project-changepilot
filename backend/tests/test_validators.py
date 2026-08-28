"""Tests for SecurityValidator, ChangePlanValidator, PatchPlanConsistencyValidator, and PatchValidator."""
from pathlib import Path
import pytest

from backend.src.models.change_plan import ChangePlan, ChangeType, ImpactedFile, PlannedChange
from backend.src.models.patch_plan import FilePatch, PatchPlan
from backend.src.repository.analyzer import FileInfo, RepositoryContext
from backend.src.validators.change_plan_validator import ChangePlanValidator
from backend.src.validators.patch_plan_consistency_validator import PatchPlanConsistencyValidator
from backend.src.validators.patch_validator import PatchValidator
from backend.src.validators.security_validator import SecurityValidator


def test_security_path_confinement_traversal(tmp_path):
    res = SecurityValidator.validate_path_confinement(tmp_path, "../outside.py")
    assert not res.passed
    assert "Path traversal" in res.errors[0]


def test_security_path_confinement_absolute(tmp_path):
    res = SecurityValidator.validate_path_confinement(tmp_path, "C:/Windows/System32/cmd.exe")
    assert not res.passed
    assert "Absolute file paths are not permitted" in res.errors[0]


def test_security_path_confinement_sensitive(tmp_path):
    res = SecurityValidator.validate_path_confinement(tmp_path, ".env")
    assert not res.passed
    assert "protected/sensitive path" in res.errors[0]


def test_security_command_safety():
    # Valid command
    res = SecurityValidator.validate_command_safety("pytest -v")
    assert res.passed

    # Injection attempts
    res_bad1 = SecurityValidator.validate_command_safety("pytest; rm -rf /")
    assert not res_bad1.passed

    res_bad2 = SecurityValidator.validate_command_safety("bash evil.sh")
    assert not res_bad2.passed


def test_change_plan_validator_success(tmp_path):
    (tmp_path / "app.py").write_text("print(1)", encoding="utf-8")
    context = RepositoryContext(
        root_path=str(tmp_path),
        primary_language="Python",
        detected_languages=["Python"],
        detected_frameworks=[],
        all_files=["app.py"],
        source_files=[FileInfo(path="app.py", size_bytes=8, is_test=False, language="Python")]
    )

    plan = ChangePlan(
        story_id="STORY-1",
        summary="Update app to support new logging",
        planned_changes=[
            PlannedChange(file_path="app.py", change_type=ChangeType.MODIFY, description="Add logging"),
            PlannedChange(file_path="new_util.py", change_type=ChangeType.CREATE, description="Create helper")
        ]
    )

    val = ChangePlanValidator.validate(plan, context)
    assert val.passed


def test_change_plan_validator_modify_nonexistent_fails(tmp_path):
    context = RepositoryContext(
        root_path=str(tmp_path),
        primary_language="Python",
        detected_languages=["Python"],
        detected_frameworks=[],
        all_files=[]
    )

    plan = ChangePlan(
        story_id="STORY-2",
        summary="Attempting to modify non-existent file",
        planned_changes=[
            PlannedChange(file_path="missing.py", change_type=ChangeType.MODIFY, description="Modify missing")
        ]
    )

    val = ChangePlanValidator.validate(plan, context)
    assert not val.passed
    assert "Cannot MODIFY file 'missing.py' because it does not exist" in val.errors[0]


def test_patch_plan_consistency_validator():
    approved_plan = ChangePlan(
        story_id="STORY-1",
        summary="Approved plan",
        planned_changes=[
            PlannedChange(file_path="app.py", change_type=ChangeType.MODIFY, description="Modify app"),
        ]
    )

    # Valid patch matching plan
    valid_patch = PatchPlan(
        story_id="STORY-1",
        summary="Valid patch",
        file_patches=[
            FilePatch(file_path="app.py", change_type=ChangeType.MODIFY, content="print(2)")
        ]
    )
    assert PatchPlanConsistencyValidator.validate(valid_patch, approved_plan).passed

    # Inconsistent patch touching unapproved file
    rogue_patch = PatchPlan(
        story_id="STORY-1",
        summary="Rogue patch",
        file_patches=[
            FilePatch(file_path="app.py", change_type=ChangeType.MODIFY, content="print(2)"),
            FilePatch(file_path="unapproved.py", change_type=ChangeType.CREATE, content="evil()")
        ]
    )
    val = PatchPlanConsistencyValidator.validate(rogue_patch, approved_plan)
    assert not val.passed
    assert "NOT approved in ChangePlan" in val.errors[0]
