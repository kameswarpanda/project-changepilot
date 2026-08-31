# ChangePilot — Autonomous Software Change & Deterministic Safety Gate Platform

[![Google Cloud Run](https://img.shields.io/badge/Google%20Cloud%20Run-Live%20Production-34A853?style=for-the-badge&logo=googlecloud&logoColor=white)](https://changepilot-189200132893.us-central1.run.app)
[![Vertex AI Gemini](https://img.shields.io/badge/Vertex%20AI-Gemini%203.5%20Flash-4285F4?style=for-the-badge&logo=googlegemini&logoColor=white)](https://cloud.google.com/vertex-ai)
[![Google Cloud SQL](https://img.shields.io/badge/Cloud%20SQL-PostgreSQL%2016-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://cloud.google.com/sql)
[![Angular 19](https://img.shields.io/badge/Frontend-Angular%2019%20%7C%20Tailwind-DD0031?style=for-the-badge&logo=angular&logoColor=white)](https://angular.dev)
[![Tests Passing](https://img.shields.io/badge/Test%20Suite-58%2F58%20Passed%20(100%25)-10B981?style=for-the-badge&logo=pytest&logoColor=white)](https://pytest.org)

> **Built for the Google All Things Agentic Hackathon**
>
> **Live Production App:** [https://changepilot-189200132893.us-central1.run.app](https://changepilot-189200132893.us-central1.run.app)  
> **Target Tracks:** *The Fortified Enterprise Fleet* • *The Taskmaster* • *Best Architectural Design*

---

## 💡 What is ChangePilot?

Most AI coding tools are static conversational chat loops requiring continuous human copy-pasting. **ChangePilot** is an enterprise-grade autonomous software change agent that operates independently:
1. Ingests natural language requirements or assigned issues from **Jira Cloud**, **Azure DevOps**, and **GitHub**.
2. Analyzes codebase topology, ASTs, and test suites across an **isolated sandbox workspace**.
3. Formulates a typed architecture plan and synthesizes atomic unified code patches with **Google Vertex AI (Gemini 3.5 Flash)**.
4. Executes real test runners (`pytest`, `npm test`, `mvn`, `cargo`, `go test`) in sandbox isolation.
5. Pushes an isolated feature branch and opens a verified **GitHub Pull Request** with test evidence and audit logs.
6. Enforces **9 deterministic safety gates** to prevent hallucination, secret leaks, and path traversal attacks.

---

## 🏛️ System Architecture

```mermaid
graph TD
    User["👤 Developer / Engineering Lead"] -->|HTTPS / Google OAuth 2.0| UI["🌐 Angular 19 Dashboard (Tailwind CSS)"]
    UI -->|REST API + JWT| Backend["⚡ FastAPI Backend Service (Google Cloud Run)"]
    
    subgraph "Google Cloud Platform (Production Environment)"
        Backend -->|SQLAlchemy Connection Pool| DB[("🗄️ Cloud SQL (PostgreSQL 16)")]
        Backend -->|Prompt & AST Context| VertexAI["🧠 Vertex AI (Gemini 3.5 Flash)"]
        Backend -->|Audit Telemetry| Logs["📊 Cloud Logging & Audit Trail"]
    end
    
    subgraph "ChangePilot 9-Stage Deterministic Pipeline"
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

## 🛡️ 9-Stage Deterministic Safety Gate Pipeline

Unlike brittle prompt-only agents, ChangePilot enforces **non-negotiable deterministic security gates**:

| Stage # | Stage Name | Responsibility & Safety Guard |
| :---: | :--- | :--- |
| **1** | **Requirement Intake** | Parameter verification, branch allowlist checking, and input sanitization. |
| **2** | **Sandbox Setup** | Creates an isolated ephemeral Git workspace (`changepilot/<story-id>-<uuid>`). Main branch is never directly mutated. |
| **3** | **Stack & Topology** | Deterministic language detection, framework analysis, and test runner discovery. |
| **4** | **Architecture Plan** | Vertex AI Gemini reasons on AST and outputs a typed `ChangePlan` (impacted files, risk rating). |
| **5** | **Safety Policy Gate** | **Zero-trust policy gate**: Rejects path traversals (`..`), sensitive files (`.env`, `id_rsa`, `.pem`), and dangerous shell operators (`&&`, `;`, `|`). |
| **6** | **AI Code Synthesis** | Synthesizes exact unified diffs conforming 1-to-1 with the approved `ChangePlan`. |
| **7** | **Patch Application** | Atomically applies file changes inside the sandbox workspace. |
| **8** | **Test Verification** | Executes real test runners with strict timeouts. Fails safely if tests break. |
| **9** | **Branch & PR Sync** | Pushes feature branch to GitHub and opens a formatted Pull Request with audit metadata. |

---

## ⚡ 1-Minute Live Demo (Try It Yourself)

1. Open the **Production App**: [https://changepilot-189200132893.us-central1.run.app](https://changepilot-189200132893.us-central1.run.app)
2. Click **"Continue with Google"** (or use any email).
3. On the **Dashboard**, click any assigned ticket from Jira/GitHub (e.g. `CP-1042: Add Percentage Discount Rule to Calculator Engine`).
4. Click **"Run ChangePilot"**.
5. Watch all **9 stages illuminate in real-time**, view the side-by-side **Unified Diff**, and inspect the created **GitHub Pull Request**!

---

## 💻 Local Quickstart & Reproduction

### Prerequisites
- Python 3.11+
- Node.js 20+ & npm
- Git

### 1. Clone & Install Backend
```bash
git clone https://github.com/kameswarpanda/project-changepilot.git
cd project-changepilot

# Setup virtual environment
python -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r backend/requirements.txt
```

### 2. Run Automated Verification Tests (58/58 Passing)
```bash
python -m pytest backend/tests/ -v
```

### 3. Run FastAPI Backend Server
```bash
python -m uvicorn backend.src.api.server:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation available at `http://localhost:8000/docs`.

### 4. Run Angular 19 Frontend
```bash
cd frontend
npm install
npm start
```
Open `http://localhost:4200` in your browser.

---

## ☁️ Google Cloud Services Utilized

- **Google Cloud Run**: Containerized backend and frontend deployments with automated autoscaling.
- **Google Cloud SQL (PostgreSQL 16)**: Multi-tenant database for user profiles, pipeline runs, and audit logs.
- **Vertex AI (Gemini 3.5 Flash)**: Foundation model for AST reasoning, impact planning, and code patch synthesis.
- **Google Cloud Logging**: Audit trail monitoring for enterprise compliance.
- **Google OAuth 2.0**: Enterprise SSO authentication.

---

## 👥 Hackathon Team & Acknowledgments

- **Developer / Creator**: Kameswar Panda
- **Hackathon**: Google All Things Agentic Hackathon on Devpost

