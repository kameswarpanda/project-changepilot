"""Repository Context Builder assembling structured, LLM-ready repository facts."""
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from backend.src.config import settings
from backend.src.repository.build_detector import BuildDetector, ToolingInfo
from backend.src.repository.impact_analyzer import ImpactAnalyzer, ImpactPrediction


class FileInfo(BaseModel):
    """Metadata about a repository file."""
    path: str
    size_bytes: int
    is_test: bool
    language: Optional[str] = None


class RepositoryContext(BaseModel):
    """Structured context extracted deterministically from the repository."""
    root_path: str
    primary_language: str
    detected_languages: List[str]
    detected_frameworks: List[str]
    detected_build_tool: Optional[str] = None
    test_runner_command: Optional[str] = None
    build_command: Optional[str] = None
    entry_points: List[str] = Field(default_factory=list)
    all_files: List[str] = Field(default_factory=list)
    source_files: List[FileInfo] = Field(default_factory=list)
    test_files: List[FileInfo] = Field(default_factory=list)
    manifest_contents: Dict[str, str] = Field(default_factory=dict)
    key_file_excerpts: Dict[str, str] = Field(default_factory=dict)
    impact_predictions: List[ImpactPrediction] = Field(default_factory=list)


class RepositoryContextBuilder:
    """Constructs comprehensive RepositoryContext combining structural facts and impact predictions."""

    @staticmethod
    def build(
        root_path: Path,
        primary_language: str,
        detected_languages: List[str],
        all_files: List[str],
        source_files: List[FileInfo],
        test_files: List[FileInfo],
        manifest_contents: Dict[str, str],
        key_file_excerpts: Dict[str, str],
        title: Optional[str] = None,
        description: Optional[str] = None
    ) -> RepositoryContext:
        """Builds a complete, validated RepositoryContext model."""
        # Detect tooling and frameworks
        tooling: ToolingInfo = BuildDetector.detect(
            root=root_path,
            primary_language=primary_language,
            manifest_contents=manifest_contents,
            all_files=all_files
        )

        # Compute impact predictions if story requirements are present
        impact_predictions: List[ImpactPrediction] = []
        if title and description:
            src_paths = [f.path for f in source_files]
            test_paths = [f.path for f in test_files]
            impact_predictions = ImpactAnalyzer.analyze_impact(
                title=title,
                description=description,
                source_files=src_paths,
                test_files=test_paths,
                file_contents=key_file_excerpts
            )

        return RepositoryContext(
            root_path=str(root_path),
            primary_language=primary_language,
            detected_languages=detected_languages,
            detected_frameworks=tooling.frameworks,
            detected_build_tool=tooling.build_tool,
            test_runner_command=tooling.test_command,
            build_command=tooling.build_command,
            entry_points=tooling.entry_points,
            all_files=all_files,
            source_files=source_files,
            test_files=test_files,
            manifest_contents=manifest_contents,
            key_file_excerpts=key_file_excerpts,
            impact_predictions=impact_predictions,
        )
