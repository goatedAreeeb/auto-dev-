# Development Phases

## Phase 1: Foundation (Days 1–2)
**Goal:** Establish the project skeleton and core sandbox logic.

| Task                                  | Owner    | Status |
| :------------------------------------ | :------- | :----- |
| Initialize monorepo with `pyproject.toml` | Backend  | [ ]    |
| Scaffold FastAPI app with placeholder routes | Backend  | [ ]    |
| Define Pydantic schemas (`DevOpsAction`, `Observation`, `StepResponse`) | Backend  | [ ]    |
| Implement `MockFilesystem` (base + overlay) | Engine   | [ ]    |
| Implement `MockProcessManager`         | Engine   | [ ]    |
| Implement command whitelist & timeout  | Engine   | [ ]    |

---

## Phase 2: Task Implementation (Days 3–4)
**Goal:** Build the three MVP tasks and their graders.

| Task                                  | Owner    | Status |
| :------------------------------------ | :------- | :----- |
| Define `t1_config` initial state + grader | Tasks    | [ ]    |
| Define `t2_port` initial state + grader   | Tasks    | [ ]    |
| Define `t3_dep` initial state + grader    | Tasks    | [ ]    |
| Wire task registry to `/reset` endpoint   | Backend  | [ ]    |
| Wire sandbox + grader into `/step` flow   | Backend  | [ ]    |
| Implement `/state` endpoint               | Backend  | [ ]    |

---

## Phase 3: Validation & Testing (Days 5–6)
**Goal:** Ensure correctness and OpenEnv compliance.

| Task                                  | Owner    | Status |
| :------------------------------------ | :------- | :----- |
| Write unit tests for sandbox engine    | QA       | [ ]    |
| Write unit tests for each grader       | QA       | [ ]    |
| Write integration tests for API routes | QA       | [ ]    |
| Run `openenv validate` locally         | QA       | [ ]    |
| Run null agent (random actions → no crash) | QA    | [ ]    |
| Run hardcoded agent (perfect solution → 1.0) | QA   | [ ]    |

---

## Phase 4: Deployment & Polish (Days 7–8)
**Goal:** Containerize and deploy to Hugging Face Spaces.

| Task                                  | Owner    | Status |
| :------------------------------------ | :------- | :----- |
| Write production `Dockerfile`          | DevOps   | [ ]    |
| Test Docker build and run locally      | DevOps   | [ ]    |
| Deploy to Hugging Face Spaces          | DevOps   | [ ]    |
| Write `README.md` with usage + API docs| Docs     | [ ]    |
| Final smoke test on live deployment    | QA       | [ ]    |

---

## Milestones Summary
| Milestone     | Deliverable                            | Target  |
| :------------ | :------------------------------------- | :------ |
| **M1**        | Sandbox engine passing unit tests       | Day 2   |
| **M2**        | All 3 tasks working end-to-end via API  | Day 4   |
| **M3**        | OpenEnv validation + agent tests pass   | Day 6   |
| **M4**        | Live on Hugging Face Spaces             | Day 8   |
