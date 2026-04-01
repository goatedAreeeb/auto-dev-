# Product Requirements Document (PRD): Auto-SRE (Junior DevOps) OpenEnv

## 1. Problem Statement
There is a need to reliably evaluate the capabilities of AI agents designed for L1 support and system recovery tasks. Current evaluations lack a realistic, safe, and easily deployable environment that mimics real-world infrastructure failures.

## 2. Solution Overview
Auto-SRE is an OpenEnv-compliant environment that provides a sandboxed, mock Linux filesystem and terminal interface. It allows researchers to safely test and benchmark "Action-LLMs" or "SRE Agents" on diagnosing and repairing simulated infrastructure issues.

## 3. Target User Persona
- **AI Researchers:** Training and evaluating reasoning agents for DevOps/SRE tasks.
- **Tools & Platform Teams:** Benchmarking the capabilities of Action-LLMs before deploying them to production systems.

## 4. Key Features & Requirements
* **Terminal Simulation Engine:** Provide a realistic bash-like interface supporting essential commands (e.g., `ls`, `cat`, `grep`, `ps`, `systemctl`, `kill`, `rm`, `mv`, `npm`).
* **Volatile Mock Filesystem:** A layered filesystem (UnionFS style) ensuring the host environment cannot be damaged, resetting cleanly between sessions.
* **Progressive Scenario Difficulty:** Support tasks of varying complexity:
  * L1: Misconfiguration fixes (e.g., file renaming).
  * L2: Process management (e.g., killing rogue processes blocking ports).
  * L3: Dependency and environment restoration.
* **OpenEnv API Compliance:** Provide standardized `/step`, `/reset`, and `/state` endpoints.
* **Deterministic, State-Based Grading:** Evaluate success based on the actual health state of the simulated services (e.g., returning HTTP 200) rather than simple text matching of the agent's commands.

## 5. Non-Functional Requirements
* **Security:** Command whitelisting and a safe mock environment to prevent host system compromise.
* **Performance:** Each action step must execute within a strict 5-second timeout to prevent indefinite hangs or infinite loops.
* **Portability:** Containerized deployment using Docker, suitable for Hugging Face Spaces.
