"""Repository Analyzer detecting project topology, languages, test frameworks, and context."""
import os
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from backend.src.config import settings


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
    all_files: List[str] = Field(default_factory=list)
    source_files: List[FileInfo] = Field(default_factory=list)
    test_files: List[FileInfo] = Field(default_factory=list)
    manifest_contents: Dict[str, str] = Field(default_factory=dict)
    key_file_excerpts: Dict[str, str] = Field(default_factory=dict)


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
        "Cargo.toml", "go.mod", "*.csproj"
    ]

    def analyze(self, workspace_path: Path) -> RepositoryContext:
        """Deterministically inspects the repository and returns rich structured context."""
        workspace_path = workspace_path.resolve()
        detected_languages: Dict[str, int] = {}
        detected_frameworks: List[str] = []
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

        # Detect Frameworks & Commands
        detected_build_tool, test_runner_cmd, build_cmd, frameworks = self._detect_tooling(
            workspace_path, primary_language, manifest_contents, all_rel_paths
        )
        detected_frameworks.extend(frameworks)

        # Read key source file excerpts (bounded for LLM context)
        for s_file in (source_files + test_files)[:15]:
            if s_file.size_bytes <= settings.max_file_size_bytes:
                fp = workspace_path / Path(s_file.path)
                try:
                    content = fp.read_text(encoding="utf-8", errors="ignore")
                    key_file_excerpts[s_file.path] = content
                except Exception:
                    pass

        return RepositoryContext(
            root_path=str(workspace_path),
            primary_language=primary_language,
            detected_languages=sorted_languages,
            detected_frameworks=detected_frameworks,
            detected_build_tool=detected_build_tool,
            test_runner_command=test_runner_cmd,
            build_command=build_cmd,
            all_files=all_rel_paths,
            source_files=source_files,
            test_files=test_files,
            manifest_contents=manifest_contents,
            key_file_excerpts=key_file_excerpts,
        )

    def _detect_tooling(
        self,
        root: Path,
        primary_lang: str,
        manifests: Dict[str, str],
        all_files: List[str]
    ) -> tuple[Optional[str], Optional[str], Optional[str], List[str]]:
        """Detects build tools, test commands, and frameworks based on manifest files."""
        frameworks: List[str] = []
        build_tool: Optional[str] = None
        test_cmd: Optional[str] = None
        build_cmd: Optional[str] = None

        if primary_lang == "Python" or any(f.endswith(".py") for f in all_files):
            build_tool = "pip"
            test_cmd = "pytest"
            frameworks.append("pytest")
            for name, content in manifests.items():
                if "fastapi" in content.lower():
                    frameworks.append("FastAPI")
                if "django" in content.lower():
                    frameworks.append("Django")
                if "flask" in content.lower():
                    frameworks.append("Flask")

        elif primary_lang in ["TypeScript", "JavaScript", "React/TypeScript", "React/JavaScript"]:
            build_tool = "npm"
            test_cmd = "npm test"
            build_cmd = "npm run build"
            if "angular.json" in manifests or any("angular" in f.lower() for f in manifests):
                frameworks.append("Angular")
                test_cmd = "npm test -- --watch=false"
            elif any("react" in content.lower() for content in manifests.values()):
                frameworks.append("React")

        elif primary_lang == "Java":
            if (root / "pom.xml").exists():
                build_tool = "Maven"
                test_cmd = "mvn test"
                build_cmd = "mvn compile"
                frameworks.append("Maven")
            elif (root / "build.gradle").exists() or (root / "build.gradle.kts").exists():
                build_tool = "Gradle"
                test_cmd = "gradle test"
                build_cmd = "gradle build"
                frameworks.append("Gradle")

        elif primary_lang == "Go":
            build_tool = "go"
            test_cmd = "go test ./..."
            build_cmd = "go build ./..."
            frameworks.append("Go Standard Toolchain")

        elif primary_lang == "Rust":
            build_tool = "cargo"
            test_cmd = "cargo test"
            build_cmd = "cargo build"
            frameworks.append("Cargo")

        elif primary_lang == "C#":
            build_tool = "dotnet"
            test_cmd = "dotnet test"
            build_cmd = "dotnet build"
            frameworks.append(".NET Core")

        return build_tool, test_cmd, build_cmd, frameworks
