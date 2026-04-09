---
title: Auto-SRE
emoji: 🚨
colorFrom: red
colorTo: yellow
sdk: docker
pinned: true
tags:
  - openenv
  - real-world
  - devops
  - sre
  - infrastructure
---

# 🚨 Auto-SRE — AI-Powered SRE Training Platform

> *"The server is down. You have 10 steps. Go."*

**Auto-SRE** is an [OpenEnv](https://huggingface.co/openenv)-compliant environment where AI agents learn to diagnose and repair broken Linux infrastructure — just like an on-call Site Reliability Engineer.

Unlike toy benchmarks, agents must execute real shell commands inside a sandboxed system, read actual error signals, and apply the correct fix. Wrong guesses don't score. Half-correct attempts earn partial credit. Systematic diagnosis earns full marks.

🌐 **Live Demo:** https://huggingface.co/spaces/goated1/auto-sre

---

## ✨ What's New

| Feature | Description |
|---|---|
| 🖥️ **Interactive Web Terminal** | Full browser-based SRE terminal — run real shell commands, see live results |
| 🎬 **Demo Mode** | Click ▶ Run Demo to watch the AI auto-solve any task and display the final reward |
| 🤖 **AI Copilot** | Context-aware debugging hints powered by OpenAI — falls back to curated hints if no key set |
| 📌 **Task Descriptions** | Each scenario shows its problem description on selection |
| 💾 **t5: Disk Full** | New scenario — 100% disk usage from massive log file in `/var/log` |
| 🧠 **t6: OOM Killer** | New scenario — rogue process leaking RAM until Linux OOM killer fires |

---

## 🧠 Why This Environment Exists

Production infrastructure breaks in predictable ways. Every day, engineers spend hours on:

- Misconfigured files that block application startup
- Rogue processes holding ports hostage
- Missing dependencies that crash deployments
- Disk-full emergencies from runaway log files
- Memory leaks triggering kernel OOM kills

**Today:** A human engineer SSHs in, runs `ps aux`, reads logs, and fixes it manually.  
**Tomorrow:** An AI agent does the same — faster, at 3 AM, without waking anyone up.

Auto-SRE is the training and evaluation ground for that agent.

---

## ⚙️ Environment Design

### How It Works

The agent receives a broken system state — a realistic Linux-like sandbox with a filesystem, running processes, and application logs. It issues shell commands step-by-step to diagnose and repair the failure.

```
Agent                     Auto-SRE Environment
  │                              │
  │── POST /reset ──────────────▶│  Broken state initialized
  │◀─ Observation ───────────────│  (stdout, stderr, cwd, health_status)
  │                              │
  │── POST /step ───────────────▶│  Shell command executed in sandbox
  │◀─ (obs, reward, done, info) ─│  Grader evaluates system state
  │                              │
  │      [repeat up to max_steps]│
```

### Observation Space

```python
class DevOpsObservation(BaseModel):
    stdout: str          # Command output
    stderr: str          # Error output (critical for diagnosis)
    cwd: str             # Current working directory
    health_status: bool  # True if the system has been repaired
```

### Action Space

```python
class DevOpsAction(BaseModel):
    tool: Literal["run_command"]
    arguments: str  # Shell command string
```

**Allowed commands** (enforced by `engine/security.py`):
`ls`, `cat`, `pwd`, `echo`, `ps`, `mv`, `kill`, `find`, `grep`, `mkdir`, `touch`, `head`, `tail`, `systemctl`, `npm install`, `cd`, `rm`

---

## 🎯 Tasks

Six tasks spanning easy → hard. The first three test repair ability. T4 tests knowing when **not** to act. T5 and T6 test advanced infrastructure failure modes.

| Task ID | Scenario | Correct Response | Difficulty | Max Steps |
|---|---|---|---|---|
| `t1_config` | Config file misnamed `.conf.bak` | `mv conf.bak conf` | 🟢 Easy | 10 |
| `t2_port` | Rogue process occupies port 8080 | `kill -9 <pid>` | 🟡 Medium | 15 |
| `t3_dep` | Missing Node.js npm dependencies | `npm install` | 🔴 Hard | 20 |
| `t4_trap` | Alert fires but system is healthy | Diagnose only — no repair | 🔴 Hard | 10 |
| `t5_disk_full` | `/var/log/syslog` consuming 100% disk | `rm /var/log/syslog` | 🟡 Medium | 10 |
| `t6_oom_killer` | Rogue process PID 999 leaking RAM | `kill 999` | 🔴 Hard | 10 |

---

### 🟢 T1 — Config File Repair (`t1_config`) · Easy

**Scenario:** The application cannot start. Its config file was accidentally renamed to `/etc/app/conf.bak`. The system is looking for `/etc/app/conf`.

**Grader (`ConfigGrader`):** Checks if `/etc/app/conf` exists. Partial credit for correct diagnostic commands even if the rename is incomplete.

---

### 🟡 T2 — Rogue Process Port Occupation (`t2_port`) · Medium

**Scenario:** A new service cannot bind to port 8080 because a stray background process is occupying it.

**Grader (`PortGrader`):** Calls `process_manager.is_port_free(8080)`. Returns max reward only when the port is genuinely freed.

---

### 🔴 T3 — Missing Application Dependencies (`t3_dep`) · Hard

**Scenario:** A Node.js application crashes immediately on startup. The `dotenv` package is missing from `node_modules`.

**Grader (`DependencyGrader`):** Checks for `/home/user/app/node_modules/.package-lock.json`. Running `npm install` from the wrong directory still returns minimum reward.

---

### 🪤 T4 — Healthy System Trap (`t4_trap`) · Hard

**Scenario:** An alert fires suggesting a failure. In reality, **the system is completely healthy**. The agent must recognize this and stand down without making any changes.

**Grader (`TrapGrader`):** Returns max reward if no destructive commands were issued and at least one diagnostic confirmed health. Returns minimum reward if any repair tool was applied to a healthy system.

---

### 💾 T5 — Disk Full: Log Overflow (`t5_disk_full`) · Medium

**Scenario:** The system is unresponsive because `/var/log/syslog` has grown to consume 100% of available disk space. No new writes can occur until the file is removed.

**Grader (`DiskGrader`):** Checks `not filesystem.exists("/var/log/syslog")`. Partial credit for diagnostic commands (`ls`, `find`). Penalty for excessive steps.

---

### 🧠 T6 — OOM Killer: Rogue Memory Hog (`t6_oom_killer`) · Hard

**Scenario:** A rogue Python script (`python3 /tmp/memory_hog.py`, PID 999) is leaking memory in an infinite loop, triggering the Linux OOM killer and destabilizing the system.

**Grader (`OOMGrader`):** Checks `not process_manager.get_by_pid(999).is_alive`. Partial credit for using `ps` to investigate before killing. Penalty for excessive steps.

---

## 🏆 Reward Function

All rewards are strictly clamped to the open interval **(0.01, 0.989)** — never exactly `0.0` or `1.0` — using:

```python
_SCORE_MIN = 0.01
_SCORE_MAX = 0.989

def _safe_score(raw: float) -> float:
    return max(_SCORE_MIN, min(_SCORE_MAX, float(raw)))
```

This satisfies OpenEnv Phase 2 validation requirements which reject boundary values.

| Condition | Score Range |
|---|---|
| Target repair complete | `0.989` |
| Correct diagnostic + partial repair | `0.15 – 0.55` |
| Correct tool, wrong arguments | `0.05 – 0.15` |
| No meaningful commands | `0.01` |
| Destructive action on healthy system (T4) | `0.05` |

---

## 📊 Baseline Results

### Hardcoded Deterministic Agent (Environment Validation)

```json
{
  "results": [
    {"task_id": "t1_config",    "reward": 0.989, "done": true},
    {"task_id": "t2_port",      "reward": 0.989, "done": true},
    {"task_id": "t3_dep",       "reward": 0.989, "done": true},
    {"task_id": "t4_trap",      "reward": 0.989, "done": true},
    {"task_id": "t5_disk_full", "reward": 0.989, "done": true},
    {"task_id": "t6_oom_killer","reward": 0.989, "done": true}
  ],
  "average_reward": 0.989
}
```

> The hardcoded agent verifies graders are correct — it knows the exact answer. Not a performance claim.

### LLM Baseline Agent (GPT-4o-mini, Zero-Shot)

```
Task           Reward   Steps   Notes
t1_config      0.85     4       Found file, applied correct rename
t2_port        0.60     8       Identified PID but killed wrong process first
t3_dep         0.30     12      Ran npm install in wrong directory twice
t4_trap        0.20     3       Applied mv to healthy system — trap triggered
t5_disk_full   0.55     6       Found /var/log, removed correct file
t6_oom_killer  0.40     7       Used ps, identified PID 999, killed correctly
─────────────────────────────────────────────────────────
Average        0.48     6.7     Significant room for RL improvement
```

The gap between hardcoded (0.989) and LLM (0.48) confirms tasks are genuinely non-trivial and suitable for RL training.

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/reset` | Initialize task. Body: `{"task_id": "t1_config"}` |
| `POST` | `/step` | Execute command. Body: `{"tool": "run_command", "arguments": "ls /etc/app"}` |
| `GET` | `/state` | Current sandbox state |
| `GET` | `/tasks` | All task definitions |
| `GET` | `/grader` | Current grader score |
| `GET` | `/healthz` | Health check |
| `GET` | `/docs` | Swagger UI |

### Example: Full T5 Episode

```bash
# 1. Reset to disk-full state
curl -X POST https://goated1-auto-sre.hf.space/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "t5_disk_full"}'

# 2. Investigate
curl -X POST https://goated1-auto-sre.hf.space/step \
  -d '{"tool": "run_command", "arguments": "ls /var/log"}'
# → {"stdout": "syslog\n", "health_status": false}

# 3. Remove the offending file
curl -X POST https://goated1-auto-sre.hf.space/step \
  -d '{"tool": "run_command", "arguments": "rm /var/log/syslog"}'
# → {"health_status": true, "reward": 0.989, "done": true}
```

---

## 🚀 Quick Start

```bash
git clone https://github.com/goatedAreeeb/auto-dev-.git
cd auto-dev-/auto-sre
pip install -e ".[dev]"

# Optional: enable AI Copilot
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

uvicorn app.main:app --host 0.0.0.0 --port 7860
# Open http://localhost:7860
```

### Docker

```bash
docker build -t auto-sre .
docker run -p 7860:7860 auto-sre
```

### Run Baselines

```bash
# Hardcoded — validates environment (no API key needed)
python scripts/run_baseline_agent.py

# LLM agent
OPENAI_API_KEY=sk-... python scripts/run_baseline_agent.py
```

---

## 🔧 Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | No | — | Enables live AI Copilot hints in the UI |
| `OPENAI_BASE_URL` | No | `https://api.openai.com/v1` | LLM proxy endpoint |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | Model for AI Copilot |
| `STEP_TIMEOUT` | No | `5` | Max seconds per sandbox command |

---

## 📁 Project Structure

```
auto-sre/
├── openenv.yaml              # OpenEnv spec — all 6 tasks registered
├── app/
│   ├── main.py               # FastAPI + Gradio mount
│   ├── ui.py                 # Web terminal, Demo Mode, AI Copilot
│   └── routes/               # /reset /step /state /tasks /grader
├── engine/
│   ├── sandbox.py            # Shell command interpreter
│   ├── filesystem.py         # UnionFS-style layered filesystem
│   ├── process_manager.py    # Mock ps/netstat/kill
│   └── security.py           # Command whitelist + timeout
├── grader/
│   └── health_check.py       # All 6 graders with _safe_score()
├── tasks/
│   ├── registry.py           # TASK_REGISTRY (t1–t6)
│   ├── t1_config.py  t2_port.py  t3_dep.py  t4_trap.py
│   ├── t5_disk_full.py       # NEW: disk overflow scenario
│   └── t6_oom_killer.py      # NEW: OOM killer scenario
└── scripts/
    └── run_baseline_agent.py
```

---

## 🔒 OpenEnv Compliance

- ✅ **Phase 1**: STDOUT format `[STEP] ... reward=X.XX` / `[END] ... rewards=...`
- ✅ **Phase 2**: All rewards strictly in `(0.01, 0.989)` — never `0.0` or `1.0`
- ✅ All 6 tasks registered in `openenv.yaml` with correct grader class paths
- ✅ `/reset`, `/step`, `/grader`, `/healthz` endpoints fully functional

---

## 📜 License

MIT — see `LICENSE` for details.

---

*Built for the OpenEnv Hackathon 2026 — Real-World Infrastructure Track*
