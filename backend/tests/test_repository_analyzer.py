"""Tests for RepositoryAnalyzer."""
from pathlib import Path
from backend.src.repository.analyzer import RepositoryAnalyzer


def test_analyze_python_repository(tmp_path):
    repo_dir = tmp_path / "py_repo"
    repo_dir.mkdir()
    (repo_dir / "calculator.py").write_text("def add(a, b): return a + b", encoding="utf-8")
    (repo_dir / "test_calculator.py").write_text("def test_add(): pass", encoding="utf-8")
    (repo_dir / "requirements.txt").write_text("pytest>=8.0.0\nfastapi", encoding="utf-8")

    analyzer = RepositoryAnalyzer()
    context = analyzer.analyze(repo_dir)

    assert context.primary_language == "Python"
    assert "pytest" in context.detected_frameworks
    assert "FastAPI" in context.detected_frameworks
    assert context.test_runner_command == "pytest"
    assert len(context.source_files) == 1
    assert len(context.test_files) == 1
    assert "requirements.txt" in context.manifest_contents
    assert "calculator.py" in context.key_file_excerpts


def test_analyze_empty_repository(tmp_path):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    analyzer = RepositoryAnalyzer()
    context = analyzer.analyze(empty_dir)

    assert context.primary_language == "Unknown"
    assert len(context.all_files) == 0
