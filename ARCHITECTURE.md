# ChangePilot — System Architecture & Design Document

[![Google Cloud Run](https://img.shields.io/badge/Google%20Cloud%20Run-Live%20Production-34A853?style=for-the-badge&logo=googlecloud&logoColor=white)](https://changepilot-189200132893.us-central1.run.app)
[![Vertex AI Gemini](https://img.shields.io/badge/Vertex%20AI-Gemini%203.5%20Flash-4285F4?style=for-the-badge&logo=googlegemini&logoColor=white)](https://cloud.google.com/vertex-ai)
[![Google Cloud SQL](https://img.shields.io/badge/Cloud%20SQL-PostgreSQL%2016-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://cloud.google.com/sql)
[![Angular 19](https://img.shields.io/badge/Frontend-Angular%2019%20%7C%20Tailwind-DD0031?style=for-the-badge&logo=angular&logoColor=white)](https://angular.dev)

---

## 1. High-Level System Architecture (HLD)

ChangePilot is built with a **Safety-First Autonomous Architecture** deployed on Google Cloud Platform. It decouples user interactions, LLM reasoning, deterministic security verification, and isolated execution.

```mermaid
graph TD
    User["👤 Developer / Engineering Lead"] -->|HTTPS / Google OAuth 2.0| UI["🌐 Angular 19 Dashboard (Tailwind CSS)"]
    UI -->|REST API + JWT Auth| Backend["⚡ FastAPI Backend Service (Google Cloud Run)"]
    
    subgraph "Google Cloud Platform (Production Environment)"
        Backend -->|SQLAlchemy Connection Pool| DB[("🗄️ Cloud SQL (PostgreSQL 16)")]
        Backend -->|Prompt & AST Context| VertexAI["🧠 Vertex AI (Gemini 3.5 Flash)"]
        Backend -->|Audit Telemetry| Logs["📊 Cloud Logging & Audit Trail"]
    end
    
    subgraph "ChangePilot 9-Stage Autonomous Engine"
        Backend --> S1["Stage 1: Requirement Intake & Boundary Check"]
        S1 --> S2["Stage 2: Sandbox Git Workspace Isolation"]
        S2 --> S3["Stage 3: Stack & AST Topology Analysis"]
        S3 --> S4["Stage 4: Gemini Architecture & Impact Plan"]
        S4 --> S5["Stage 5: Deterministic Safety Policy Gate"]
        S5 --> S6["Stage 6: AI Unified Patch Synthesis"]
        S6 --> S7["Stage 7: Sandboxed Patch Application"]
        S7 --> S8["Stage 8: Automated Test & Build Runner"]
        S8 --> S9["Stage 9: Branch Sync & GitHub Pull Request"]
    end
    
    S9 -->|GitHub REST API| GitHub["🐙 GitHub Enterprise / Repositories"]
```

---

## 2. The 9-Stage Deterministic Safety Gate Pipeline

The core architectural innovation of ChangePilot is the **Deterministic Safety Gate Pipeline**. Unlike standard conversational AI tools that blindly execute code, ChangePilot forces every proposed change through 9 sequential gates:

| Stage # | Stage Name | Technical Action | Safety Enforcement |
| :---: | :--- | :--- | :--- |
| **1** | **Requirement Intake** | Parses user story, Jira issue, or GitHub issue parameters. | Validates branch allowlists and sanitizes input boundaries. |
| **2** | **Sandbox Setup** | Clones target repository into a temporary isolated workspace. | Creates an ephemeral Git branch (`changepilot/<story-id>-<uuid>`). Main branch is never mutated directly. |
| **3** | **Stack & Topology** | Analyzes repository AST, manifests, package managers, and test runners. | Auto-detects `pytest`, `npm test`, `mvn`, `cargo`, `go test`, or static web structures. |
| **4** | **Architecture Plan** | **Vertex AI (Gemini 3.5 Flash)** reasons on the AST to formulate a typed `ChangePlan`. | Maps impacted files, required modifications, and structural risks before writing code. |
| **5** | **Safety Policy Gate** | Deterministic security validator checks the proposed plan against zero-trust policies. | **Hard-blocks** path traversals (`..`), secret files (`.env`, `id_rsa`, `.pem`), and command injection operators. |
| **6** | **AI Code Synthesis** | Gemini synthesizes atomic unified diffs strictly conforming to the approved plan. | Patches are verified for syntactic integrity and structural consistency. |
| **7** | **Patch Application** | Filesystem mutation boundary applies additions, edits, and deletions atomically. | Enforces strict path confinement (`resolved_path.relative_to(workspace_root)`). |
| **8** | **Test Verification** | Executes real test suites inside the isolated workspace with strict timeouts. | Captures complete stdout/stderr. Fails safely if tests break or regressions occur. |
| **9** | **Branch & PR Sync** | Pushes feature branch to GitHub and opens a formatted Pull Request. | Includes comprehensive description, test evidence, and full audit logs. |

---

## 3. Data Flow & Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Developer
    participant UI as Angular 19 UI
    participant API as FastAPI Backend (Cloud Run)
    participant DB as Cloud SQL (PostgreSQL)
    participant VertexAI as Vertex AI (Gemini 3.5 Flash)
    participant Sandbox as Isolated Workspace Sandbox
    participant GitHub as GitHub REST API

    Developer->>UI: Submit Ticket / Select Story
    UI->>API: POST /api/execute (ChangeRequestPayload)
    API->>DB: Record Execution Started (RUNNING)
    API->>Sandbox: Stage 1-2: Clone & Isolate Git Branch
    API->>Sandbox: Stage 3: Inspect AST & Build Tools
    API->>VertexAI: Stage 4: Generate ChangePlan (AST + Requirements)
    VertexAI-->>API: Return Structured ChangePlan
    API->>API: Stage 5: Deterministic Safety Validation (Pass/Reject)
    API->>VertexAI: Stage 6: Synthesize Unified Code Patches
    VertexAI-->>API: Return FilePatch Objects
    API->>Sandbox: Stage 7: Apply Patches to Workspace
    API->>Sandbox: Stage 8: Run Automated Test Suites (pytest/npm)
    Sandbox-->>API: Test Results (100% Pass / Fail)
    API->>GitHub: Stage 9: Push Branch & Open Pull Request
    GitHub-->>API: PR # created with diff & test evidence
    API->>DB: Save Final Run & Audit Trail (SUCCESS)
    API-->>UI: Stream Live Stage Duration & Unified Diff
    UI-->>Developer: Display Diffs, Audit Logs & PR Link
```

---

## 4. Threat Model & Security Boundaries

ChangePilot is built according to **Zero-Trust Engineering Principles**:

1. **Path Confinement**: All file modifications resolve absolute paths and mathematically verify `resolved.relative_to(workspace_root)`. Path traversal attacks (`../../etc/passwd`, `C:\Windows`) fail closed immediately.
2. **Command Injection Prevention**: Shell chaining characters (`;`, `&&`, `||`, ``` ` ```, `$`, `>`, `<`) are blocked by the security validator before subprocess invocation.
3. **Secret Protection**: Protected file patterns (`.env`, `*.pem`, `id_rsa`, `*.key`, `credentials.json`) are forbidden from being modified, read, or included in patches.
4. **Isolated Ephemeral Sandboxing**: Workspaces are created in isolated temporary directories with guaranteed cleanup in `finally` blocks upon completion or failure.
5. **Role-Based Access Control (RBAC)**: All API endpoints are protected with Google OAuth 2.0 and JWT token authentication.

---

## 5. Google Cloud Infrastructure Topology

* **Google Cloud Run**: Serverless container execution hosting the containerized FastAPI backend and Angular frontend.
* **Google Cloud SQL (PostgreSQL 16)**: High-availability relational database storing multi-tenant user accounts, assigned tickets, pipeline execution runs, and audit logs.
* **Google Vertex AI (Gemini 3.5 Flash)**: Foundation model provider handling whole-codebase AST reasoning, change plan formulation, and unified code diff generation.
* **Google Cloud Logging**: Centralized, structured audit log aggregation for enterprise traceability.
