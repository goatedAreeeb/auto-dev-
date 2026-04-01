# System Architecture

## 1. Architectural Overview
Auto-SRE follows a modular architecture integrating an OpenEnv-compliant API with a sandboxed mock system execution engine. The environment simulates a volatile Linux filesystem and process space, effectively isolating agent actions from the host OS.

## 2. Core Components
### 2.1 The API Layer
* **Technology:** FastAPI, Pydantic v2.
* **Responsibility:** Exposes the OpenEnv API endpoints (`/step`, `/reset`, `/state`). Validates incoming `DevOpsAction` payloads using Pydantic schemas and serializes the `Observation` responses.

### 2.2 The Sandbox Engine
* **Technology:** Python-based shell simulator.
* **Responsibility:** Parses and executes the shell commands requested by the agent. It enforces security mechanisms:
  * **Command Whitelisting:** Only safe mock commands are implemented.
  * **Timeout Enforcement:** A strict 5-second boundary per execution to prevent DOS via infinite loops.
  * **Path Resolution:** Translates mock paths to the internal filesystem structure.

### 2.3 The State Manager (Filesystem & Processes)
* **Technology:** In-memory dictionary overlay (UnionFS pattern).
* **Responsibility:** Maintains the "truth" of the mock system.
  * Uses a read-only base layer for standard Linux directories.
  * Uses a mutable write layer for agent-driven modifications.
  * Tracks metadata of mock processes (e.g., which ports are occupied).

### 2.4 The Grader Module
* **Technology:** Python scripts/functions tailored per task.
* **Responsibility:** Runs a Health Check independently of the agent's observation loop. It interrogates the State Manager to verify if the specific goal conditions (e.g., configuration file exists, port is freed, app runs) have been met to determine the reward.

## 3. Data Flow Diagram
1. **Agent** sends `DevOpsAction(run_command, "kill -9 123")` -> **API Layer**.
2. **API Layer** validates and passes command to -> **Sandbox Engine**.
3. **Sandbox Engine** applies security checks -> updates **State Manager** (removes process ID 123).
4. **Sandbox Engine** generates `stdout`/`stderr` -> triggers **Grader Module**.
5. **Grader Module** assesses state -> computes `Reward` and `health_status`.
6. **API Layer** returns `Observation` (including stdout, health_status, reward) -> **Agent**.
