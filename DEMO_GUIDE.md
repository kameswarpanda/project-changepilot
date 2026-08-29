# ChangePilot — Hackathon Judge Presentation Guide (5–10 Minutes)

> **Presentation Narrative:** Most AI coding tools operate as unconstrained chat bots with no deterministic safety boundaries, leading to hallucinated changes, broken builds, security vulnerabilities, or unintended file deletions. **ChangePilot** re-architects AI software development into a **deterministic, typed, sandboxed 9-stage engineering pipeline**.

---

## ⏱️ 5-Minute Live Presentation Script

### 1. The Core Problem (Minute 1)
* **The Challenge:** LLMs cannot be trusted to blindly edit files or run uncontrolled shell commands on production or developer machines.
* **The Solution:** ChangePilot implements an autonomous software-change platform with **strict trust boundaries**:
  * AI acts as an advisor proposing typed plans (`ChangePlan`, `PatchPlan`).
  * Deterministic software enforces safety gates (Path Confinement, Plan Consistency, Command Whitelists).
  * Modifications happen strictly on isolated Git branches in temporary sandboxes.
  * Changes are only declared successful if real automated tests pass 100%.

---

### 2. Live Platform Demonstration (Minutes 2–3)

#### Step A: Open the Enterprise Dashboard
* URL: `http://localhost:4200` (or `http://localhost:8000`)
* Highlight the UI features:
  * **9-Stage Autonomous Stepper:** Visual real-time indicator from `WORKSPACE_READY` to `COMPLETED`.
  * **KPI Metrics Row:** Total runs, success rate (100%), average duration (~2.1s), safety violations prevented, and connected repositories.
  * **Active Execution Card:** Live story parameters and target repo location.

#### Step B: Execute the Canonical Demo Scenario
1. Select Story Template: **"CP-DEMO-1: Add optional flat monetary discount to calculator"**
2. Click **⚡ Run Autonomous Pipeline**
3. Observe real-time transition across the 9 stages:
   * **Stage 1 (Workspace):** Git clone & branch isolation (`changepilot/CP-DEMO-1-...`).
   * **Stage 2 (Analysis):** Multi-ecosystem analysis detects Python, pytest, manifests.
   * **Stage 3 (Plan Generated):** Change Analyst generates structured `ChangePlan`.
   * **Stage 4 (Plan Gate):** ChangePlan verified against repository facts.
   * **Stage 5 (Patch Generated):** Code Generator creates complete `FilePatch` models.
   * **Stage 6 (Patch Gate):** Patch consistency & path confinement verified.
   * **Stage 7 (Applied):** Safe filesystem mutation on isolated branch + Git commit.
   * **Stage 8 (Tests):** Bounded `pytest` runner executes inside the sandbox.
   * **Stage 9 (Completed):** Complete verification & auditable diff synthesis.

#### Step C: Inspect the Verification Modal
* Click **"View Full Report"**:
  * **Unified Git Diff:** Color-coded additions (`+`) and deletions (`-`) showing backward-compatible `calculate_total` and new `apply_discount`.
  * **Structured ChangePlan:** Technical summary, impacted files with AI confidence scores, risk analysis, and testing strategy.
  * **Test Output Logs:** Direct stdout/stderr from pytest (7 passed in 0.04s).
  * **Audit Trail:** Millisecond-accurate timestamped log of each validation gate.

---

### 3. Demonstrating Deterministic Safety & Adversarial Protection (Minute 4)

Switch to the **Template Selector** or show terminal tests:
* **Scenario: Path Traversal Attack (`../../etc/passwd`):**
  * Gate `SecurityValidator.validate_path_confinement` rejects the attempt before any disk access.
* **Scenario: Rogue AI File Generation (Unapproved file in PatchPlan):**
  * Gate `PatchPlanConsistencyValidator` blocks the unapproved file from being written.
* **Scenario: Command Injection (`pytest; rm -rf /`):**
  * Gate `SecurityValidator.validate_command_safety` detects shell chaining metacharacters and aborts execution.

---

### 4. Fast CLI Demo Fallback (Minute 5)

If presenting from the terminal, execute:
```bash
python run_demo.py
```
This runs the complete 9-stage pipeline headlessly and outputs the colorized audit trail, stage latencies, unified diff, and pytest verification in ~2 seconds.

---

## 🛠️ Verification & Run Commands Summary

| Action | Command |
| :--- | :--- |
| **Run Full Test Suite (39 Tests)** | `pytest backend/tests -v` |
| **Run Headless CLI Demo** | `python run_demo.py` |
| **Start FastAPI Backend** | `start_backend.bat` or `python -m uvicorn backend.src.api.server:app --port 8000` |
| **Start Angular UI** | `start_frontend.bat` or `cd frontend && npm start` |
| **Build Docker Container** | `docker build -t changepilot:latest .` |
