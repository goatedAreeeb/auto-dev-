# User Stories and Acceptance Criteria

## Epic 1: Environment Safety and Sandboxing
**User Story:** As an AI researcher, I want my agent to interact with a mock filesystem so that it cannot damage the host machine during testing.
* **Acceptance Criteria:**
  * The system uses a UnionFS-style layered filesystem.
  * Base `/etc`, `/var`, etc. are read-only.
  * Agent writes are stored in a temporary write layer.
  * Dangerous commands (e.g., `rm -rf /` on the host) are intercepted and contained within the sandbox.

## Epic 2: API and Interaction
**User Story:** As an agent framework developer, I want to use standard OpenEnv API endpoints so that I can easily integrate Auto-SRE into my existing evaluation harness.
* **Acceptance Criteria:**
  * The system exposes a `/reset` endpoint that restores the broken baseline state.
  * The system exposes a `/step` endpoint that accepts a `DevOpsAction` and returns an `Observation`.
  * The `Observation` contains `stdout/stderr`, `cwd`, and `health_status`.
  * A 5-second timeout is enforced per `/step`.

## Epic 3: Scenarios and Tasks
**User Story:** As an evaluator, I want the environment to support progressive difficulty levels so I can test the limits of my agent's reasoning.
* **Acceptance Criteria:**
  * Task `t1_config`: System presents a misnamed config file. The agent must `mv` it to the right place.
  * Task `t2_port`: Port 8080 is occupied. The agent must find and `kill` the offending process.
  * Task `t3_dep`: Missing dependencies prevent app startup. The agent must run `npm install`.

## Epic 4: Verification and Grading
**User Story:** As a researcher, I want objective grading based on system health so that I can accurately measure if the agent actually fixed the problem.
* **Acceptance Criteria:**
  * The grader checks file existence for `t1_config`.
  * The grader verifies port availability for `t2_port`.
  * The grader executes the target app and checks for success for `t3_dep`.
  * Rewards are given based on these health checks, providing partial credit for diagnosis and full credit for restoration.
