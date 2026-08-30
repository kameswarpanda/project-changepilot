"""Security Validator enforcing path confinement, command safety, and secret protection."""
import os
from pathlib import Path
from typing import List, Optional
from backend.src.config import settings
from backend.src.models.workflow_result import ValidationResult


class SecurityValidator:
    """Deterministic security gate enforcing strict boundaries before any workspace mutation."""

    # Disallowed dangerous chaining operators in commands
    SHELL_INJECTION_OPERATORS = [";", "&&", "||", "`", "$", ">", "<", "\n", "\r", "|"]

    # Allowed test runner binaries
    ALLOWED_COMMAND_BINARIES = {
        "pytest", "python", "python3", "npm", "npx", "mvn", "gradle", "cargo", "go", "dotnet", "make", "ctest"
    }

    # Protected sensitive filenames/extensions
    SENSITIVE_PATTERNS = [
        ".git", ".env", ".aws", ".gcp", "id_rsa", "id_ed25519", "credentials", "secrets", ".key", ".pem"
    ]

    @classmethod
    def validate_path_confinement(cls, workspace_root: Path, relative_file_path: str) -> ValidationResult:
        """Verifies that the target path strictly resolves inside the workspace root."""
        clean_rel = relative_file_path.strip().replace("\\", "/")

        if not clean_rel:
            return ValidationResult(
                validator_name="SecurityValidator.validate_path_confinement",
                passed=False,
                errors=["Target file path cannot be empty."]
            )

        # Explicitly check for directory traversal attempts
        parts = [p for p in clean_rel.split("/") if p]
        if ".." in parts:
            return ValidationResult(
                validator_name="SecurityValidator.validate_path_confinement",
                passed=False,
                errors=[f"Path traversal sequence '..' detected in path: {relative_file_path}"]
            )

        if clean_rel.startswith("/") or clean_rel.startswith("\\") or (len(clean_rel) > 1 and clean_rel[1] == ":"):
            return ValidationResult(
                validator_name="SecurityValidator.validate_path_confinement",
                passed=False,
                errors=[f"Absolute file paths are not permitted: {relative_file_path}"]
            )

        # Check against disallowed sensitive patterns
        for part in parts:
            p_lower = part.lower()
            # Explicit protection for internal git repo folder
            if p_lower == ".git":
                return ValidationResult(
                    validator_name="SecurityValidator.validate_path_confinement",
                    passed=False,
                    errors=["Operation on protected/sensitive path pattern '.git' is forbidden."]
                )
            # Protection for environment files (.env, .env.production, etc.)
            if p_lower == ".env" or p_lower.startswith(".env."):
                return ValidationResult(
                    validator_name="SecurityValidator.validate_path_confinement",
                    passed=False,
                    errors=["Operation on protected/sensitive path pattern '.env' is forbidden."]
                )
            # Protection for secret keys, credentials, and private keys
            if any(p_lower.endswith(ext) for ext in [".key", ".pem", ".pkcs12", ".pfx"]):
                return ValidationResult(
                    validator_name="SecurityValidator.validate_path_confinement",
                    passed=False,
                    errors=[f"Operation on protected/sensitive path pattern '{part}' is forbidden."]
                )
            if p_lower in ["id_rsa", "id_ed25519", "id_ecdsa", "id_dsa", "credentials.json", "service_account.json"]:
                return ValidationResult(
                    validator_name="SecurityValidator.validate_path_confinement",
                    passed=False,
                    errors=[f"Operation on protected/sensitive path pattern '{part}' is forbidden."]
                )
            if p_lower in [".aws", ".gcp", ".ssh", "secrets"]:
                return ValidationResult(
                    validator_name="SecurityValidator.validate_path_confinement",
                    passed=False,
                    errors=[f"Operation on protected/sensitive path pattern '{part}' is forbidden."]
                )

        # Resolve path and verify confinement to workspace root
        try:
            resolved_root = workspace_root.resolve()
            resolved_target = (workspace_root / clean_rel).resolve()

            # Ensure target is within root
            resolved_target.relative_to(resolved_root)
        except (ValueError, Exception) as e:
            return ValidationResult(
                validator_name="SecurityValidator.validate_path_confinement",
                passed=False,
                errors=[f"Path resolves outside of isolated workspace root: {str(e)}"]
            )

        return ValidationResult(
            validator_name="SecurityValidator.validate_path_confinement",
            passed=True,
            details={"resolved_path": str(resolved_target)}
        )

    @classmethod
    def validate_command_safety(cls, command: str) -> ValidationResult:
        """Validates that a test/build command is safe and allowlisted."""
        cmd_str = command.strip()

        if not cmd_str:
            return ValidationResult(
                validator_name="SecurityValidator.validate_command_safety",
                passed=False,
                errors=["Command cannot be empty."]
            )

        # Split into tokens safely
        tokens = cmd_str.split()
        if not tokens:
            return ValidationResult(
                validator_name="SecurityValidator.validate_command_safety",
                passed=False,
                errors=["Command has no executable specified."]
            )

        executable = Path(tokens[0]).name.lower()
        if executable.endswith(".exe"):
            executable = executable[:-4]

        if executable not in cls.ALLOWED_COMMAND_BINARIES:
            return ValidationResult(
                validator_name="SecurityValidator.validate_command_safety",
                passed=False,
                errors=[f"Command binary '{executable}' is not in the approved safe list."]
            )

        # Check for dangerous command chaining characters in arguments
        for op in cls.SHELL_INJECTION_OPERATORS:
            if op in cmd_str:
                return ValidationResult(
                    validator_name="SecurityValidator.validate_command_safety",
                    passed=False,
                    errors=[f"Dangerous shell chaining operator '{op}' detected in command."]
                )

        return ValidationResult(
            validator_name="SecurityValidator.validate_command_safety",
            passed=True,
            details={"executable": executable, "command": cmd_str}
        )
