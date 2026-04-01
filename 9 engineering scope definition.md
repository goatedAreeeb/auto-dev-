# Engineering Scope Definition

## 1. In-Scope (MVP)
| Area                     | Details                                                                 |
| :----------------------- | :---------------------------------------------------------------------- |
| **OpenEnv API**          | `/step`, `/reset`, `/state` endpoints fully compliant with the OpenEnv spec |
| **Sandbox Engine**       | Python-based mock shell supporting `ls`, `cat`, `grep`, `ps`, `kill`, `mv`, `systemctl`, `npm` |
| **Mock Filesystem**      | Dictionary-based UnionFS overlay with base (read-only) and write layers  |
| **Mock Process Manager** | In-memory process table with PID and port-binding tracking               |
| **3 MVP Tasks**          | `t1_config` (file rename), `t2_port` (port conflict), `t3_dep` (dependency install) |
| **Deterministic Grading**| Per-task health-check functions returning normalized rewards              |
| **Containerized Deploy** | Dockerfile for local dev and Hugging Face Spaces deployment              |
| **Validation Scripts**   | Null agent (crash test) and hardcoded agent (score verification)         |

---

## 2. Out-of-Scope (Post-MVP)
| Area                        | Reason for Deferral                                           |
| :-------------------------- | :------------------------------------------------------------ |
| **Real filesystem access**  | Security risk; mock is sufficient for evaluation              |
| **Multi-agent support**     | Not required for initial benchmarking                         |
| **GPU-based execution**     | All tasks are CPU-only shell operations                       |
| **Persistent leaderboard**  | Nice-to-have; can be added as a Gradio UI layer later         |
| **Network simulation**      | Mock HTTP checks are sufficient; no real TCP needed           |
| **Custom task authoring UI**| Tasks are defined in Python; no GUI needed for MVP            |

---

## 3. Assumptions & Constraints
* Python 3.10+ is the only supported runtime.
* The host machine provides Docker for containerized deployment.
* Hugging Face Spaces (free tier) is the primary deployment target.
* Each agent step must complete within 5 seconds.
* The environment is single-tenant (one agent session at a time for MVP).

---

## 4. Dependencies
| Dependency     | Version  | Purpose                              |
| :------------- | :------- | :----------------------------------- |
| `fastapi`      | ≥0.100   | API framework                        |
| `pydantic`     | ≥2.0     | Request/response schema validation   |
| `uvicorn`      | ≥0.23    | ASGI server                          |
| `httpx`        | ≥0.24    | Async HTTP client for testing        |
| `pytest`       | ≥7.0     | Test runner                          |
| `ruff`         | ≥0.1     | Linting and formatting               |
