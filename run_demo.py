"""Headless E2E Demo Runner for ChangePilot (Hackathon Presentation Script)."""
import os
import sys
import time
from pathlib import Path
from colorama import Fore, Style, init

# Ensure stdout supports UTF-8 on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure backend modules are on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.src.models.change_request import ChangeRequest
from backend.src.models.workflow_result import WorkflowStatus
from backend.src.workflow.orchestrator import WorkflowOrchestrator

init(autoreset=True)


def print_banner():
    print(f"\n{Fore.CYAN}{'=' * 75}")
    print(f"{Fore.CYAN}{Style.BRIGHT}  [*] ChangePilot - Autonomous Software-Change Platform (Demo Runner)")
    print(f"{Fore.CYAN}{'=' * 75}\n")


def run_demo():
    print_banner()
    demo_repo = Path(__file__).resolve().parent / "demo_repo"

    print(f"{Fore.YELLOW}[Target Repository]:{Style.RESET_ALL} {demo_repo}")
    print(f"{Fore.YELLOW}[Story ID]:{Style.RESET_ALL} CP-DEMO-1")
    print(f"{Fore.YELLOW}[Change Title]:{Style.RESET_ALL} Add optional flat monetary discount to calculator")
    print(f"{Fore.YELLOW}[Requirements]:{Style.RESET_ALL} Backward compatible calculate_total, reject negative discounts and excessive discounts, update unit tests.\n")

    request = ChangeRequest(
        story_id="CP-DEMO-1",
        title="Add optional flat monetary discount to calculator",
        description=(
            "Add an optional flat monetary discount parameter to the calculate_total function. "
            "Preserve existing callers when discount is None. Reject negative discounts and "
            "discounts greater than calculated total with ValueError. Update unit tests."
        ),
        repository_location=str(demo_repo)
    )

    orchestrator = WorkflowOrchestrator()
    print(f"{Fore.MAGENTA}>> Starting 9-Stage Autonomous Pipeline...\n")
    start_time = time.time()

    result = orchestrator.execute(request)
    elapsed = round(time.time() - start_time, 2)

    print(f"\n{Fore.CYAN}{'=' * 75}")
    print(f"{Fore.CYAN}{Style.BRIGHT}  STAGE AUDIT TRAIL & DETERMINISTIC GATES")
    print(f"{Fore.CYAN}{'=' * 75}")

    for idx, stage in enumerate(result.audit_trail, 1):
        status_color = Fore.GREEN if stage.status == WorkflowStatus.SUCCESS else Fore.RED
        dur = f"({stage.duration_ms}ms)" if stage.duration_ms else ""
        print(f"  {Fore.LIGHTBLACK_EX}[{idx:02d}] {status_color}{stage.stage.value:<18} {Style.BRIGHT}{stage.status.value:<10}{Style.RESET_ALL} {dur:<10} {stage.message}")

    print(f"\n{Fore.CYAN}{'=' * 75}")
    print(f"{Fore.CYAN}{Style.BRIGHT}  VERIFICATION RESULTS")
    print(f"{Fore.CYAN}{'=' * 75}")

    print(f"  Status:         {Fore.GREEN if result.success else Fore.RED}{Style.BRIGHT}{result.status.value}")
    print(f"  Total Duration: {result.total_duration_ms}ms")
    print(f"  Tests Passed:   {Fore.GREEN if result.test_passed else Fore.RED}{result.test_passed}")
    print(f"  Branch Created: {Fore.BLUE}{result.branch_name}")

    if result.applied_diff:
        print(f"\n{Fore.CYAN}{'=' * 75}")
        print(f"{Fore.CYAN}{Style.BRIGHT}  UNIFIED GIT DIFF (GENERATED & APPLIED)")
        print(f"{Fore.CYAN}{'=' * 75}")
        for line in result.applied_diff.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                print(f"{Fore.GREEN}{line}")
            elif line.startswith("-") and not line.startswith("---"):
                print(f"{Fore.RED}{line}")
            elif line.startswith("@@"):
                print(f"{Fore.CYAN}{line}")
            else:
                print(f"{Style.DIM}{line}")

    if result.test_output:
        print(f"\n{Fore.CYAN}{'=' * 75}")
        print(f"{Fore.CYAN}{Style.BRIGHT}  AUTOMATED TEST SUITE EXECUTION")
        print(f"{Fore.CYAN}{'=' * 75}")
        print(f"{Style.DIM}{result.test_output.strip()}")

    print(f"\n{Fore.GREEN}{Style.BRIGHT}* Autonomous pipeline execution finished successfully in {elapsed}s!\n")


if __name__ == "__main__":
    run_demo()
