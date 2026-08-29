"""Unit tests for multi-ecosystem repository intelligence, build detection, and impact analysis."""
import pytest
from pathlib import Path

from backend.src.repository.build_detector import BuildDetector
from backend.src.repository.context_builder import FileInfo, RepositoryContextBuilder
from backend.src.repository.impact_analyzer import ImpactAnalyzer


def test_build_detector_python(tmp_path):
    """Test Python build detector with poetry and FastAPI."""
    manifests = {
        "pyproject.toml": '[tool.poetry]\nname = "demo"\n\n[dependencies]\nfastapi = "^0.110.0"'
    }
    all_files = ["pyproject.toml", "main.py", "test_main.py"]

    info = BuildDetector.detect(tmp_path, "Python", manifests, all_files)
    assert info.build_tool == "poetry"
    assert "FastAPI" in info.frameworks
    assert "pytest" in info.frameworks
    assert "main.py" in info.entry_points


def test_build_detector_typescript_angular(tmp_path):
    """Test Angular frontend detector."""
    manifests = {
        "package.json": '{"dependencies": {"@angular/core": "^19.0.0"}}',
        "angular.json": '{"projects": {"app": {}}}'
    }
    all_files = ["package.json", "angular.json", "src/main.ts", "src/app/app.component.spec.ts"]

    info = BuildDetector.detect(tmp_path, "TypeScript", manifests, all_files)
    assert info.build_tool == "npm"
    assert "Angular" in info.frameworks
    assert "src/main.ts" in info.entry_points or "main.ts" in info.entry_points


def test_build_detector_java_maven(tmp_path):
    """Test Java Maven repository detector."""
    manifests = {
        "pom.xml": '<project><dependencies><dependency><groupId>org.springframework.boot</groupId></dependency></dependencies></project>'
    }
    all_files = ["pom.xml", "src/main/java/App.java", "src/test/java/AppTest.java"]

    info = BuildDetector.detect(tmp_path, "Java", manifests, all_files)
    assert info.build_tool == "Maven"
    assert info.test_framework == "JUnit"
    assert "Spring Boot" in info.frameworks


def test_build_detector_go(tmp_path):
    """Test Go module detector."""
    manifests = {"go.mod": "module example.com/calc\n\ngo 1.22"}
    all_files = ["go.mod", "main.go", "calc_test.go"]

    info = BuildDetector.detect(tmp_path, "Go", manifests, all_files)
    assert info.build_tool == "go"
    assert "go test" in info.test_command
    assert "main.go" in info.entry_points


def test_build_detector_rust_cargo(tmp_path):
    """Test Rust Cargo detector."""
    manifests = {"Cargo.toml": '[package]\nname = "demo"'}
    all_files = ["Cargo.toml", "src/main.rs"]

    info = BuildDetector.detect(tmp_path, "Rust", manifests, all_files)
    assert info.build_tool == "cargo"
    assert "cargo test" in info.test_command
    assert "src/main.rs" in info.entry_points


def test_impact_analyzer_keyword_matching():
    """Test impact prediction based on title, description, and source keywords."""
    title = "Add discount feature to calculator"
    desc = "Modify calculate_total to support discount coupons and add tests in test_calculator"
    source_files = ["calculator.py", "auth.py", "database.py"]
    test_files = ["test_calculator.py", "test_auth.py"]
    contents = {
        "calculator.py": "def calculate_total(items): return sum(items)",
        "auth.py": "def authenticate(user): pass",
        "test_calculator.py": "def test_calc(): pass",
    }

    predictions = ImpactAnalyzer.analyze_impact(title, desc, source_files, test_files, contents)

    assert len(predictions) >= 2
    top_predicted = predictions[0]
    assert "calculator" in top_predicted.file_path.lower()
    assert top_predicted.confidence >= 0.8


def test_repository_context_builder(tmp_path):
    """Test RepositoryContextBuilder assembling structured facts."""
    src = FileInfo(path="calculator.py", size_bytes=500, is_test=False, language="Python")
    tst = FileInfo(path="test_calculator.py", size_bytes=400, is_test=True, language="Python")

    context = RepositoryContextBuilder.build(
        root_path=tmp_path,
        primary_language="Python",
        detected_languages=["Python"],
        all_files=["calculator.py", "test_calculator.py"],
        source_files=[src],
        test_files=[tst],
        manifest_contents={"requirements.txt": "pytest>=8.0.0"},
        key_file_excerpts={"calculator.py": "def add(a, b): return a + b"},
        title="Add subtract function",
        description="Add subtract logic to calculator"
    )

    assert context.primary_language == "Python"
    assert context.detected_build_tool == "pip"
    assert context.test_runner_command == "pytest"
    assert len(context.impact_predictions) > 0
