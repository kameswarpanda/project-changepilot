"""Validation Engine running bounded, isolated test/build verification."""
import logging
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field

from backend.src.config import settings
from backend.src.validators.security_validator import SecurityValidator

logger = logging.getLogger("changepilot.executor.validation_engine")


class CommandExecutionResult(BaseModel):
    """Result of running a test or build command."""
    command: str
    return_code: int
    success: bool
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool = False
    error: Optional[str] = None


class ValidationEngine:
    """Bounded, deterministic test and build executor."""

    @classmethod
    def run_command(
        cls,
        command: str,
        working_directory: Path,
        timeout_seconds: Optional[int] = None,
        custom_env: Optional[dict] = None
    ) -> CommandExecutionResult:
        """Executes an allowlisted verification command inside the workspace."""
        timeout = timeout_seconds or settings.command_timeout_seconds
        working_directory = working_directory.resolve()

        # Security gate
        sec_check = SecurityValidator.validate_command_safety(command)
        if not sec_check.passed:
            return CommandExecutionResult(
                command=command,
                return_code=-1,
                success=False,
                stdout="",
                stderr="",
                duration_seconds=0.0,
                error=f"Security rejection: {'; '.join(sec_check.errors)}"
            )

        # Prepare clean environment with active virtual environment on PATH
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        
        # Ensure venv/scripts is at front of PATH
        scripts_dir = str(Path(sys.executable).parent)
        current_path = env.get("PATH", "")
        if scripts_dir not in current_path:
            env["PATH"] = f"{scripts_dir}{os.pathsep}{current_path}"

        if custom_env:
            env.update(custom_env)

        # Remove sensitive tokens from environment passed to subprocess
        for k in ["GEMINI_API_KEY", "GOOGLE_API_KEY", "AWS_SECRET_ACCESS_KEY", "GITHUB_TOKEN"]:
            env.pop(k, None)

        logger.info(f"Executing '{command}' in {working_directory} (timeout: {timeout}s)")
        start_time = time.time()

        try:
            # Tokenize command
            tokens = shlex.split(command, posix=(os.name != "nt"))
            
            # If executable is pytest and sys.executable is available, run via python -m pytest
            if tokens and tokens[0] == "pytest":
                tokens = [sys.executable, "-m", "pytest"] + tokens[1:]
            elif tokens and tokens[0] in ["python", "python3"]:
                tokens = [sys.executable] + tokens[1:]

            process = subprocess.run(
                tokens,
                cwd=str(working_directory),
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
                encoding="utf-8",
                errors="replace"
            )

            duration = round(time.time() - start_time, 2)
            success = (process.returncode == 0)

            logger.info(f"Command '{command}' finished with code {process.returncode} in {duration}s")
            return CommandExecutionResult(
                command=command,
                return_code=process.returncode,
                success=success,
                stdout=process.stdout or "",
                stderr=process.stderr or "",
                duration_seconds=duration,
                timed_out=False
            )

        except subprocess.TimeoutExpired as te:
            duration = round(time.time() - start_time, 2)
            stdout = te.stdout or ""
            stderr = te.stderr or ""
            logger.error(f"Command '{command}' timed out after {timeout} seconds")
            return CommandExecutionResult(
                command=command,
                return_code=-1,
                success=False,
                stdout=stdout if isinstance(stdout, str) else stdout.decode("utf-8", errors="ignore"),
                stderr=stderr if isinstance(stderr, str) else stderr.decode("utf-8", errors="ignore"),
                duration_seconds=duration,
                timed_out=True,
                error=f"Command execution timed out after {timeout} seconds."
            )

        except Exception as e:
            duration = round(time.time() - start_time, 2)
            logger.error(f"Command execution failed: {e}")
            return CommandExecutionResult(
                command=command,
                return_code=-1,
                success=False,
                stdout="",
                stderr="",
                duration_seconds=duration,
                error=f"Subprocess execution error: {str(e)}"
            )
