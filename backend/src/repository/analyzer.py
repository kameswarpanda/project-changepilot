"""Repository Analyzer detecting project topology, languages, test frameworks, and context."""
import os
from pathlib import Path
from typing import Dict, List, Optional

from backend.src.config import settings
from backend.src.repository.context_builder import FileInfo, RepositoryContext, RepositoryContextBuilder


class RepositoryAnalyzer:
    """Deterministic analyzer extracting language, framework, test commands, and structure."""

    LANGUAGE_EXTENSIONS = {
        ".py": "Python",
        ".ts": "TypeScript",
        ".js": "JavaScript",
        ".jsx": "React/JavaScript",
        ".tsx": "React/TypeScript",
        ".java": "Java",
        ".cs": "C#",
        ".go": "Go",
        ".rs": "Rust",
        ".cpp": "C++",
        ".c": "C",
        ".rb": "Ruby",
        ".php": "PHP",
        ".html": "HTML",
        ".css": "CSS",
        ".scss": "SCSS",
        ".json": "JSON",
        ".yaml": "YAML",
        ".yml": "YAML",
    }

    IGNORED_DIRS = {
        ".git", ".venv", "venv", "env", "node_modules", "__pycache__",
        "dist", "build", "target", "bin", "obj", ".idea", ".vscode", ".pytest_cache"
    }

    MANIFEST_FILES = [
        "pyproject.toml", "requirements.txt", "setup.py", "Pipfile",
        "package.json", "angular.json", "tsconfig.json",
        "pom.xml", "build.gradle", "build.gradle.kts",
        "Cargo.toml", "go.mod", "*.csproj", "CMakeLists.txt", "Makefile"
    ]

    def analyze(
        self,
        workspace_path: Path,
        title: Optional[str] = None,
        description: Optional[str] = None
    ) -> RepositoryContext:
        """Deterministically inspects the repository and returns rich structured context."""
        workspace_path = workspace_path.resolve()
        detected_languages: Dict[str, int] = {}
        source_files: List[FileInfo] = []
        test_files: List[FileInfo] = []
        all_rel_paths: List[str] = []
        manifest_contents: Dict[str, str] = {}
        key_file_excerpts: Dict[str, str] = {}

        # Scan filesystem
        for root, dirs, files in os.walk(workspace_path):
            # Prune ignored directories
            dirs[:] = [d for d in dirs if d not in self.IGNORED_DIRS and not d.startswith(".")]

            for file_name in files:
                full_path = Path(root) / file_name
                try:
                    rel_path = str(full_path.relative_to(workspace_path)).replace("\\", "/")
                except ValueError:
                    continue

                all_rel_paths.append(rel_path)
                ext = full_path.suffix.lower()
                lang = self.LANGUAGE_EXTENSIONS.get(ext)
                if lang:
                    detected_languages[lang] = detected_languages.get(lang, 0) + 1

                is_test = (
                    "test" in file_name.lower()
                    or "spec" in file_name.lower()
                    or "/tests/" in f"/{rel_path}/"
                    or "/test/" in f"/{rel_path}/"
                )

                file_info = FileInfo(
                    path=rel_path,
                    size_bytes=full_path.stat().st_size if full_path.exists() else 0,
                    is_test=is_test,
                    language=lang
                )

                if is_test:
                    test_files.append(file_info)
                elif lang:
                    source_files.append(file_info)

                # Capture manifest contents
                if file_name in self.MANIFEST_FILES or any(file_name.endswith(m.replace("*", "")) for m in self.MANIFEST_FILES if "*" in m):
                    try:
                        if full_path.stat().st_size <= 50_000:
                            manifest_contents[rel_path] = full_path.read_text(encoding="utf-8", errors="ignore")
                    except Exception:
                        pass

        # Sort languages by frequency
        sorted_languages = sorted(detected_languages.keys(), key=lambda k: detected_languages[k], reverse=True)
        primary_language = sorted_languages[0] if sorted_languages else "Unknown"

        # Read key source file excerpts (bounded for LLM context)
        for s_file in (source_files + test_files)[:20]:
            if s_file.size_bytes <= settings.max_file_size_bytes:
                fp = workspace_path / Path(s_file.path)
                try:
                    content = fp.read_text(encoding="utf-8", errors="ignore")
                    key_file_excerpts[s_file.path] = content
                except Exception:
                    pass

        # Delegate context synthesis to RepositoryContextBuilder
        return RepositoryContextBuilder.build(
            root_path=workspace_path,
            primary_language=primary_language,
            detected_languages=sorted_languages,
            all_files=all_rel_paths,
            source_files=source_files,
            test_files=test_files,
            manifest_contents=manifest_contents,
            key_file_excerpts=key_file_excerpts,
            title=title,
            description=description
        )
