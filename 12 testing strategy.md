# Testing Strategy

## 1. Testing Pyramid
```
         ┌──────────────┐
         │   E2E Tests   │  ← Agent-level smoke tests
         ├──────────────┤
         │  Integration  │  ← API route + engine + grader
         ├──────────────┤
         │  Unit Tests   │  ← Individual modules
         └──────────────┘
```

---

## 2. Unit Tests
**Tool:** `pytest`

### 2.1 Sandbox Engine (`tests/test_sandbox.py`)
| Test Case                        | Assertion                                      |
| :------------------------------- | :--------------------------------------------- |
| Execute whitelisted command      | Returns expected `stdout`                      |
| Execute blacklisted command      | Raises `CommandNotAllowedError`                |
| Command exceeds timeout          | Raises `TimeoutError` after 5 seconds          |
| `mv` updates overlay filesystem  | File appears at new path in write layer        |
| `kill` removes process           | Process no longer in active process list        |

### 2.2 Filesystem (`tests/test_filesystem.py`)
| Test Case                        | Assertion                                      |
| :------------------------------- | :--------------------------------------------- |
| Read from base layer             | Returns correct file content                   |
| Write creates overlay entry      | File exists in overlay, base unchanged         |
| `ls` lists merged view           | Returns union of base + overlay files          |
| Path traversal blocked           | `../../etc/passwd` resolves safely within mock |

### 2.3 Grader (`tests/test_grader.py`)
| Test Case                        | Assertion                                      |
| :------------------------------- | :--------------------------------------------- |
| `t1` config file exists          | Returns `reward = 1.0`                         |
| `t1` config file missing         | Returns `reward = 0.0`                         |
| `t2` port 8080 freed             | Returns `reward = 1.0`                         |
| `t2` port 8080 still occupied    | Returns `reward = 0.0`                         |
| `t3` app runs successfully       | Returns `reward = 1.0`                         |
| `t3` deps installed but app fails| Returns `reward = 0.5`                         |

---

## 3. Integration Tests
**Tool:** `pytest` + `httpx.AsyncClient`

### 3.1 API Routes (`tests/test_api.py`)
| Test Case                            | Assertion                                    |
| :----------------------------------- | :------------------------------------------- |
| `POST /reset` with valid `task_id`   | Returns 200, `health_status == false`        |
| `POST /reset` with invalid `task_id` | Returns 404                                  |
| `POST /step` with valid action       | Returns 200, contains `observation` + `reward`|
| `POST /step` with disallowed command | Returns 400                                  |
| `GET /state`                         | Returns current `task_id` and `step_count`   |

### 3.2 Full Episode Flow (`tests/test_tasks.py`)
| Test Case                            | Assertion                                    |
| :----------------------------------- | :------------------------------------------- |
| Reset → solve t1 → check reward      | Final `reward == 1.0`, `done == true`        |
| Reset → solve t2 → check reward      | Final `reward == 1.0`, `done == true`        |
| Reset → solve t3 → check reward      | Final `reward == 1.0`, `done == true`        |
| Reset → exceed max steps             | Episode ends, `done == true`, partial reward |

---

## 4. End-to-End / Agent Tests
**Tool:** Custom Python scripts (`scripts/`)

### 4.1 Null Agent (`scripts/run_null_agent.py`)
* Sends random commands from the whitelist for 100 steps.
* **Pass criteria:** No unhandled exceptions, no server crashes, `StepResponse` always returned.

### 4.2 Hardcoded Agent (`scripts/run_hardcoded_agent.py`)
* Sends the known correct solution for each task.
* **Pass criteria:** `reward == 1.0` and `done == true` for all 3 tasks.

---

## 5. Compliance Testing
**Tool:** `openenv validate`

| Check                            | Assertion                                       |
| :------------------------------- | :---------------------------------------------- |
| Schema compliance                | Action/Observation schemas match OpenEnv spec    |
| Endpoint availability            | `/step`, `/reset`, `/state` respond correctly    |
| Determinism                      | Same sequence of actions → same final reward     |

---

## 6. Coverage Targets
| Module       | Target Coverage |
| :----------- | :-------------- |
| `engine/`    | ≥ 90%           |
| `grader/`    | ≥ 95%           |
| `app/routes/`| ≥ 85%           |
| `tasks/`     | ≥ 90%           |
| **Overall**  | **≥ 85%**       |
