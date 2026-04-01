# Information Architecture

## 1. Top-Level Structure
Auto-SRE is structured around the OpenEnv standard, providing a clear contract for inputs and outputs.

### 1.1 Inputs (Action Space)
* **`DevOpsAction` Object**
  * `tool`: The identifier of the tool being used (e.g., `run_command`).
  * `arguments`: A string representing the precise shell command the agent wishes to execute.

### 1.2 Outputs (Observation Space)
* **`Observation` Object**
  * `stdout`: The standard output stream from the executed command.
  * `stderr`: The standard error stream from the executed command.
  * `cwd`: The current working directory after the command executes.
  * `health_status`: A boolean flag representing the health of the simulated infrastructure.

### 1.3 Endpoints
* `POST /step`: Takes `DevOpsAction`, returns `Observation`.
* `POST /reset`: Reinitializes the environment to the target task's starting state.
* `GET /state`: Retrieves the current metadata and general status of the mock environment.

## 2. Internal Domains
### 2.1 Filesystem State
* **Base Dictionary:** Represents the immutable structure of a Linux system (`/etc`, `/var`, `/usr`).
* **Overlay Dictionary:** Represents the mutable state modified by the agent during the session.

### 2.2 Process Tree State
* A mock representation of running processes (`PID`, `COMMAND`, `PORT_BINDINGS`).
* Updated by commands like `kill` or starting mock services.

### 2.3 Task Definitions
* Contains the initial "broken" state (files, processes).
* Contains the specific grader function to evaluate the "fixed" state.
