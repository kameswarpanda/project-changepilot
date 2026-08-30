"""Build and test tooling detector across multiple programming ecosystems."""
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel


class ToolingInfo(BaseModel):
    """Information about detected build and test tooling."""
    build_tool: Optional[str] = None
    build_command: Optional[str] = None
    test_framework: Optional[str] = None
    test_command: Optional[str] = None
    frameworks: List[str] = []
    entry_points: List[str] = []


class BuildDetector:
    """Detects programming languages, frameworks, build systems, and test frameworks."""

    @staticmethod
    def detect(
        root: Path,
        primary_language: str,
        manifest_contents: Dict[str, str],
        all_files: List[str]
    ) -> ToolingInfo:
        """Deterministically detects build tools, test runners, frameworks, and entry points."""
        frameworks: List[str] = []
        build_tool: Optional[str] = None
        build_cmd: Optional[str] = None
        test_framework: Optional[str] = None
        test_cmd: Optional[str] = None
        entry_points: List[str] = []

        manifest_keys = [k.lower() for k in manifest_contents.keys()]
        all_files_lower = [f.lower() for f in all_files]

        # -------------------------------------------------------------
        # 1. Java Ecosystem (Maven / Gradle / Spring Boot)
        # -------------------------------------------------------------
        if primary_language == "Java" or "pom.xml" in manifest_keys or any("gradle" in k for k in manifest_keys) or any(f.endswith(".java") for f in all_files):
            if "pom.xml" in manifest_keys or (root / "pom.xml").exists() or any("pom.xml" in f for f in all_files_lower):
                build_tool = "Maven"
                build_cmd = "mvn compile"
                test_framework = "JUnit"
                test_cmd = "mvn test"
                if "Maven" not in frameworks:
                    frameworks.append("Maven")
            elif any(f in manifest_keys for f in ["build.gradle", "build.gradle.kts"]) or any("build.gradle" in f for f in all_files_lower):
                build_tool = "Gradle"
                build_cmd = "gradle build"
                test_framework = "JUnit"
                test_cmd = "gradle test"
                if "Gradle" not in frameworks:
                    frameworks.append("Gradle")
            else:
                build_tool = "javac"
                test_cmd = "mvn test"

            # Check Spring Boot & frameworks
            is_spring = False
            for _, content in manifest_contents.items():
                content_lower = content.lower()
                if "org.springframework" in content_lower or "spring-boot" in content_lower:
                    is_spring = True
                if "quarkus" in content_lower and "Quarkus" not in frameworks:
                    frameworks.append("Quarkus")
                if "micronaut" in content_lower and "Micronaut" not in frameworks:
                    frameworks.append("Micronaut")

            if is_spring or any("application.properties" in f or "application.yml" in f for f in all_files_lower):
                if "Spring Boot" not in frameworks:
                    frameworks.append("Spring Boot")
            if "JUnit" not in frameworks:
                frameworks.append("JUnit")

            for candidate in ["src/main/java", "src/test/java"]:
                if any(candidate in f for f in all_files):
                    entry_points.append(candidate)

        # -------------------------------------------------------------
        # 2. Python Ecosystem
        # -------------------------------------------------------------
        elif primary_language == "Python" or any(f.endswith(".py") for f in all_files):
            build_tool = "pip"
            test_framework = "pytest"
            test_cmd = "pytest"
            frameworks.append("pytest")

            # Check Poetry / Pipenv / Hatch / Flit
            if "pyproject.toml" in manifest_keys:
                content = manifest_contents.get("pyproject.toml", "")
                if "tool.poetry" in content:
                    build_tool = "poetry"
                    build_cmd = "poetry build"
                    test_cmd = "poetry run pytest"
                elif "tool.flit" in content:
                    build_tool = "flit"
                elif "tool.hatch" in content:
                    build_tool = "hatch"

            if "pipfile" in manifest_keys:
                build_tool = "pipenv"
                test_cmd = "pipenv run pytest"

            # Detect web/application frameworks
            for _, content in manifest_contents.items():
                content_lower = content.lower()
                if "fastapi" in content_lower and "FastAPI" not in frameworks:
                    frameworks.append("FastAPI")
                if "django" in content_lower and "Django" not in frameworks:
                    frameworks.append("Django")
                if "flask" in content_lower and "Flask" not in frameworks:
                    frameworks.append("Flask")
                if "pydantic" in content_lower and "Pydantic" not in frameworks:
                    frameworks.append("Pydantic")
                if "unittest" in content_lower and "pytest" not in frameworks:
                    test_framework = "unittest"
                    test_cmd = "python -m unittest discover"

            # Entry points
            for candidate in ["main.py", "app.py", "server.py", "cli.py", "manage.py"]:
                if any(f.endswith(candidate) for f in all_files):
                    entry_points.append(candidate)

        # -------------------------------------------------------------
        # 3. JavaScript / TypeScript / Frontend Ecosystem
        # -------------------------------------------------------------
        elif primary_language in ["TypeScript", "JavaScript", "React/TypeScript", "React/JavaScript"] or "package.json" in manifest_keys:
            build_tool = "npm"
            test_framework = "jest"
            test_cmd = "npm test"
            build_cmd = "npm run build"

            pkg_content = manifest_contents.get("package.json", "")
            pkg_lower = pkg_content.lower()

            if "yarn.lock" in all_files_lower:
                build_tool = "yarn"
                test_cmd = "yarn test"
                build_cmd = "yarn build"
            elif "pnpm-lock.yaml" in all_files_lower:
                build_tool = "pnpm"
                test_cmd = "pnpm test"
                build_cmd = "pnpm build"

            # Frameworks
            if "angular.json" in manifest_keys or "@angular/core" in pkg_lower:
                frameworks.append("Angular")
                test_framework = "karma/jasmine"
                test_cmd = "npm test -- --watch=false"
            elif "react" in pkg_lower:
                frameworks.append("React")
                if "next" in pkg_lower:
                    frameworks.append("Next.js")
            elif "vue" in pkg_lower:
                frameworks.append("Vue.js")
            elif "express" in pkg_lower:
                frameworks.append("Express.js")
            elif "nest" in pkg_lower:
                frameworks.append("NestJS")

            if "vitest" in pkg_lower:
                test_framework = "vitest"
                test_cmd = "npx vitest run"
            elif "jest" in pkg_lower:
                test_framework = "jest"
                test_cmd = "npm test -- --watchAll=false"

            for candidate in ["index.ts", "index.js", "main.ts", "main.js", "app.ts", "app.js", "src/main.ts", "src/index.ts"]:
                if any(f.lower() == candidate for f in all_files):
                    entry_points.append(candidate)

        # -------------------------------------------------------------
        # 4. Go Ecosystem
        # -------------------------------------------------------------
        elif primary_language == "Go":
            build_tool = "go"
            build_cmd = "go build ./..."
            test_framework = "go test"
            test_cmd = "go test -v ./..."
            frameworks.append("Go Modules")
            if any(f.endswith("main.go") for f in all_files):
                entry_points.append("main.go")

        # -------------------------------------------------------------
        # 5. Rust Ecosystem
        # -------------------------------------------------------------
        elif primary_language == "Rust":
            build_tool = "cargo"
            build_cmd = "cargo build"
            test_framework = "cargo test"
            test_cmd = "cargo test"
            frameworks.append("Cargo")
            if any(f.endswith("main.rs") for f in all_files):
                entry_points.append("src/main.rs")
            if any(f.endswith("lib.rs") for f in all_files):
                entry_points.append("src/lib.rs")

        # -------------------------------------------------------------
        # 6. C# / .NET Ecosystem
        # -------------------------------------------------------------
        elif primary_language == "C#":
            build_tool = "dotnet"
            build_cmd = "dotnet build"
            test_framework = "xUnit/NUnit"
            test_cmd = "dotnet test"
            frameworks.append(".NET")
            if any(f.endswith("Program.cs") for f in all_files):
                entry_points.append("Program.cs")

        # -------------------------------------------------------------
        # 7. C / C++ Ecosystem
        # -------------------------------------------------------------
        elif primary_language in ["C++", "C"]:
            if "cmakelists.txt" in manifest_keys:
                build_tool = "CMake"
                build_cmd = "cmake --build build"
                test_cmd = "ctest --test-dir build"
                frameworks.append("CMake")
            elif "makefile" in manifest_keys:
                build_tool = "Make"
                build_cmd = "make"
                test_cmd = "make test"
                frameworks.append("Makefile")

        return ToolingInfo(
            build_tool=build_tool,
            build_command=build_cmd,
            test_framework=test_framework,
            test_command=test_cmd,
            frameworks=frameworks,
            entry_points=entry_points
        )
