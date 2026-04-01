# Database Schema

## 1. Overview
Auto-SRE is primarily an **in-memory, stateless simulation**. It does not use a traditional relational database. Instead, the "schema" refers to the in-memory data structures that represent the mock system state. These structures are serialized via Pydantic v2 models.

---

## 2. Core Data Models (Pydantic Schemas)

### 2.1 `MockFile`
Represents a single file in the mock filesystem.

| Field        | Type     | Description                                      |
| :----------- | :------- | :----------------------------------------------- |
| `path`       | `str`    | Absolute path within the mock filesystem          |
| `content`    | `str`    | File content (text-based)                         |
| `permissions`| `str`    | Unix-style permission string (e.g., `rw-r--r--`) |
| `is_readonly`| `bool`   | Whether the file belongs to the base (read-only) layer |

### 2.2 `MockProcess`
Represents a running process in the mock environment.

| Field          | Type       | Description                                    |
| :------------- | :--------- | :--------------------------------------------- |
| `pid`          | `int`      | Process ID                                     |
| `command`      | `str`      | Command string that started the process        |
| `port_bindings`| `list[int]`| List of network ports bound by this process    |
| `is_alive`     | `bool`     | Whether the process is currently running       |

### 2.3 `EnvironmentState`
The root-level snapshot of the entire mock system.

| Field            | Type               | Description                                   |
| :--------------- | :----------------- | :-------------------------------------------- |
| `filesystem`     | `dict[str, MockFile]` | Full overlay filesystem (base + writes)     |
| `processes`      | `list[MockProcess]`   | Currently active mock processes             |
| `cwd`            | `str`              | Agent's current working directory              |
| `task_id`        | `str`              | Identifier of the active task scenario         |
| `step_count`     | `int`              | Number of steps taken in the current episode   |

### 2.4 `TaskDefinition`
Stores the blueprint for each scenario.

| Field            | Type       | Description                                       |
| :--------------- | :--------- | :------------------------------------------------ |
| `task_id`        | `str`      | Unique task identifier (e.g., `t1_config`)        |
| `description`    | `str`      | Human-readable description of the failure          |
| `initial_state`  | `EnvironmentState` | The "broken" baseline state              |
| `grader_fn`      | `Callable` | Reference to the grading function for this task    |
| `max_steps`      | `int`      | Maximum allowed steps before timeout               |

---

## 3. Session / Episode Storage (Optional Persistence)
For leaderboard or analytics purposes, a lightweight store (SQLite or JSON file) can track:

| Field          | Type     | Description                              |
| :------------- | :------- | :--------------------------------------- |
| `session_id`   | `str`    | UUID for the episode                     |
| `task_id`      | `str`    | Which task was attempted                 |
| `agent_name`   | `str`    | Identifier of the agent being evaluated  |
| `total_steps`  | `int`    | Steps consumed                           |
| `final_reward` | `float`  | Normalized reward (0.0 – 1.0)           |
| `timestamp`    | `datetime`| When the episode was completed          |
