# Scoring Engine Specification

## 1. Philosophy
The scoring engine uses **deterministic, state-based grading** — it evaluates whether the simulated infrastructure has been repaired, not whether the agent typed the "right" command. This approach is more robust and less gameable than keyword matching.

---

## 2. Reward Structure

### 2.1 Reward Range
All rewards are normalized to `[0.0, 1.0]`.

### 2.2 Reward Breakdown
| Component            | Weight | Description                                                |
| :------------------- | :----- | :--------------------------------------------------------- |
| **Diagnostic Credit** | 0.3   | Awarded for actions that gather useful information (e.g., `ls`, `cat`, `ps aux`) before attempting a fix. |
| **Fix Credit**        | 0.7   | Awarded when the grader's health check passes, confirming the service is restored. |

### 2.3 Penalties
| Condition                | Penalty  | Description                                 |
| :----------------------- | :------- | :------------------------------------------ |
| Exceeding `max_steps`    | Episode ends, reward frozen | No additional reward after limit |
| Disallowed command       | `0.0` for that step | Command rejected, no state change   |
| Timeout (5s per step)    | `0.0` for that step | Step aborted                        |

---

## 3. Per-Task Grader Functions

### 3.1 `t1_config` — Misnamed Config
```python
def grade_t1(state: EnvironmentState) -> float:
    """Check if /etc/app/conf exists (was renamed from conf.bak)."""
    if "/etc/app/conf" in state.filesystem:
        return 1.0  # Full fix credit
    if any("conf" in cmd for cmd in state.command_history):
        return 0.3  # Partial diagnostic credit
    return 0.0
```

### 3.2 `t2_port` — Port 8080 Occupied
```python
def grade_t2(state: EnvironmentState) -> float:
    """Check if port 8080 is free."""
    occupied = any(8080 in p.port_bindings for p in state.processes if p.is_alive)
    if not occupied:
        return 1.0
    return 0.0
```

### 3.3 `t3_dep` — Missing Dependency
```python
def grade_t3(state: EnvironmentState) -> float:
    """Check if the app successfully starts (dependencies installed)."""
    if state.app_run_success:
        return 1.0
    if "node_modules" in state.filesystem:
        return 0.5  # Installed but app didn't start cleanly
    return 0.0
```

---

## 4. Scoring Flow
1. Agent submits `DevOpsAction` via `/step`.
2. Sandbox Engine executes the action and updates `EnvironmentState`.
3. Grader Module runs the appropriate `grade_tX()` function.
4. Computed `reward` and `done` flag are returned in the `StepResponse`.
5. If `done == True` or `step_count >= max_steps`, the episode terminates.

---

## 5. Leaderboard Metrics (Optional)
| Metric              | Formula                                  |
| :------------------ | :--------------------------------------- |
| **Success Rate**    | `episodes_with_reward_1 / total_episodes`|
| **Avg Steps**       | `sum(steps) / total_episodes`            |
| **Efficiency Score**| `reward / steps_taken` (higher is better)|
