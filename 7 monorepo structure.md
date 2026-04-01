# Monorepo Structure

## 1. Overview
The project is organized as a single repository with clear separation between the environment engine, task definitions, grading logic, and deployment configuration.

---

## 2. Directory Layout
```
auto-sre/
├── README.md
├── pyproject.toml                 # Project metadata & dependencies
├── Dockerfile                     # Container build for HF Spaces / local
├── docker-compose.yml             # Multi-service orchestration (optional)
├── .env.example                   # Environment variable template
│
├── app/                           # ── FastAPI Application ──
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry point, CORS, lifespan
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── step.py                # POST /step endpoint
│   │   ├── reset.py               # POST /reset endpoint
│   │   └── state.py               # GET  /state endpoint
│   └── schemas/
│       ├── __init__.py
│       ├── action.py              # DevOpsAction model
│       └── observation.py         # Observation, StepResponse models
│
├── engine/                        # ── Sandbox Engine ──
│   ├── __init__.py
│   ├── sandbox.py                 # Shell command parser & executor
│   ├── filesystem.py              # MockFilesystem (base + overlay)
│   ├── process_manager.py         # MockProcess tree management
│   └── security.py                # Command whitelist, timeout wrapper
│
├── grader/                        # ── Grading Module ──
│   ├── __init__.py
│   ├── base.py                    # Abstract grader interface
│   └── health_check.py            # Concrete health-check implementations
│
├── tasks/                         # ── Task Definitions ──
│   ├── __init__.py
│   ├── registry.py                # Task registry (lookup by task_id)
│   ├── t1_config.py               # Task: misnamed config file
│   ├── t2_port.py                 # Task: occupied port
│   └── t3_dep.py                  # Task: missing dependency
│
├── tests/                         # ── Test Suite ──
│   ├── __init__.py
│   ├── test_sandbox.py
│   ├── test_grader.py
│   ├── test_api.py
│   └── test_tasks.py
│
└── scripts/                       # ── Utility Scripts ──
    ├── validate_openenv.sh        # Run `openenv validate`
    ├── run_null_agent.py          # Random-action agent for crash testing
    └── run_hardcoded_agent.py     # Solution agent for score verification
```

---

## 3. Key Conventions
| Convention            | Rule                                                    |
| :-------------------- | :------------------------------------------------------ |
| **Python version**    | 3.10+                                                   |
| **Package manager**   | `pip` via `pyproject.toml` (PEP 621)                    |
| **Linting**           | `ruff` for linting and formatting                       |
| **Type checking**     | `mypy` with strict mode                                 |
| **Testing**           | `pytest` with `httpx` for async API tests               |
| **Branching**         | `main` (stable) → `dev` (integration) → feature branches|
