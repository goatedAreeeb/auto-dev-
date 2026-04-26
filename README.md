---
title: Auto-SRE
emoji: 🚨
colorFrom: indigo
colorTo: purple
sdk: docker
pinned: false
---

# 🚨 Auto-SRE — AI-Powered SRE Training Platform

[![OpenEnv Compliant](https://img.shields.io/badge/OpenEnv-Phase%201%20%26%202%20Compliant-brightgreen)](https://huggingface.co/spaces/goated1/auto-sre)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-Hugging%20Face%20Spaces-blue)](https://huggingface.co/spaces/goated1/auto-sre)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> *"The server is down. You have 15 steps. Go."*

## 🎯 Problem Motivation

Modern infrastructure failures cost companies millions per hour of downtime, yet on-call SRE engineers are woken at 3 AM to manually SSH in, run `ps aux`, read logs, and apply fixes they've seen a hundred times before. These workflows are repetitive, high-stakes, and perfectly structured for automation — yet no open benchmark existed to train and evaluate AI agents on realistic, multi-step Linux repair tasks. **Auto-SRE** fills that gap: a fully sandboxed, reward-instrumented SRE environment where language models learn to diagnose cascading failures, kill rogue processes, fix broken configs, and restore services, using the same shell commands a human engineer would use — without any human in the loop.

**Auto-SRE** is an [OpenEnv](https://huggingface.co/openenv)-compliant environment where AI agents learn to diagnose and repair broken Linux infrastructure — just like an on-call Site Reliability Engineer.

Unlike toy benchmarks, agents must execute real shell commands inside a sandboxed system, read actual error signals, and apply the correct fix — **in the correct order**. Wrong guesses don't score. Half-correct attempts earn partial credit. Systematic diagnosis earns full marks.

🌐 **Live Demo:** [Try it on Hugging Face Spaces](https://huggingface.co/spaces/goated1/auto-sre)  
**Hugging Face Blog:**[See Our Exciting  Blog](https://huggingface.co/spaces/goated1/auto-sre/blob/main/Blog.md)
📄 **Writeup:** [OpenEnv India 2026 Submission](https://huggingface.co/spaces/goated1/auto-sre)

---

## 🤖 What the Agent Sees, Does, and Gets Rewarded For

At each step of an episode the agent receives an **observation** (stdout + stderr from its last command, current working directory, and a `health_status` boolean). From this observation the agent issues a single shell command chosen from a whitelisted set (`ls`, `cat`, `ps`, `kill`, `mv`, `rm`, `systemctl`, `echo`, `find`, `df`, `free`, `top`, and more). The environment executes the command against a stateful mock Linux sandbox, mutates world-model variables (`disk_usage`, `memory_usage`, `services_running`, `rogue_pid`), and returns an **intermediate reward** reflecting how much closer the system is to a healthy state — earned only through real state changes, never by matching command strings. A final **terminal reward** from the grader summarises full episode success, clamped strictly to (0.01, 0.989) per OpenEnv Phase 2 requirements. The agent that learns to read the environment's signals — rather than hardcode sequences — achieves the highest rewards.

---

## ✨ What's New (v2.0)

| Feature | Description |
|---|---|
| 🆕 **T7–T10 Hard Tasks** | 4 new enterprise-grade failure scenarios |
| 🤖 **Multi-Agent System** | Commander → Planner → Executor → Critic pipeline |
| 📈 **RL Training Pipeline** | Unsloth + TRL GRPO across all 10 tasks with reward curve |
| 🔗 **Dependency Ordering** | T9: wrong restart sequence is penalized |
| 🔐 **Secret Injection** | T10: echo redirection writes to config files |
| 📊 **Per-Task Metrics** | Training plots per-task reward + overall curve |

---

## 🎯 What is Auto-SRE?

Auto-SRE is an interactive Site Reliability Engineering (SRE) training and evaluation environment built for the OpenEnv hackathon. It provides:

- A **mock Linux sandbox** where AI agents or humans diagnose and fix broken infrastructure
- A **FastAPI backend** fully compliant with OpenEnv Phase 1 & Phase 2 validation
- An **interactive web terminal UI** built with Gradio
- An **AI Copilot** that provides context-aware debugging hints on demand
- A **Demo Mode** that auto-plays the optimal solution for each task

Agents will face challenges such as:
- Misconfigured files that block application startup
- Rogue processes holding ports hostage
- Missing dependencies that crash deployments
- Disk-full emergencies from runaway log files
- Memory leaks triggering kernel OOM kills
- Cascading failures across service dependency chains

**Today:** A human engineer SSHs in, runs `ps aux`, reads logs, and fixes it manually.
**Tomorrow:** An AI agent does the same — faster, at 3 AM, without waking anyone up.

Auto-SRE is the training and evaluation ground for that agent.

---

## ✨ Features

### 🖥️ Interactive Web Terminal
A fully functional browser-based terminal where you can run shell commands like a real SRE:
- `ls`, `cat`, `ps`, `kill`, `mv`, `rm`, `find`, `grep`, `npm install`, `systemctl`, and more
- Real-time reward score and system health display
- Command history log


### 🎬 Demo Mode
Click **▶ Run Demo** to watch the AI solve any task automatically, showing the optimal command sequence and final reward score. Guarantees judges always see a successful resolution.

### 🤖 AI Copilot
Click **🤖 Ask AI Copilot for Hint** to get a context-aware debugging hint:
- Reads your current task and command history from the UI
- Queries OpenAI (if configured) for a personalized 1-2 line hint
- Falls back gracefully to curated static hints if no API key is set
- **100% UI-isolated** — does not touch the backend or affect rewards

### 📌 Task Descriptions
Each scenario shows its description immediately on selection, so judges and users understand the problem context instantly.

---

## 🗂️ Scenario Tasks

<img width="1456" height="937" alt="image" src="https://github.com/user-attachments/assets/768a0267-2bb5-49bc-8be8-50afb44d7c22" />
<img width="1211" height="949" alt="image" src="https://github.com/user-attachments/assets/9ce5a3b5-4a2a-4abe-948a-4fec75462c86" />



---

## 📊 Validation Report & Agent Comparison

**Validation Results:**
* API_STATUS: PASS
* TASKS_STATUS: PASS
* EDGE_TESTS: PASS
* DETERMINISM: PASS
* RL_READY: PASS
* OVERALL: PASS

**Agent Comparison:**
- **Null agent** → Performs random or empty behavior (low base reward).
- **Hardcoded agent** → Fixed paths; achieves only partial success with randomized environment states.
- **Multi-agent system** → Demonstrates adaptive reasoning (Commander, Planner, Executor, Critic) to evaluate and recover dynamically.
- **Baseline agent** → Optimal state-machine controller, achieving near-optimal performance (~0.97 average reward) across all tasks.

---

## 🧠 Reinforcement Learning Support

Auto-SRE fully supports training Language Models via reinforcement learning. We explicitly target **Theme #2 (Long-Horizon Instruction Following via Script Generation)**.
- A **GRPO training pipeline** is already implemented (`scripts/train_grpo.py`).
- The pipeline demonstrates **Open-Loop Script Generation**, forcing the model to generate the entire sequential bash script upfront to simulate extreme long-horizon planning where intermediate execution feedback is unavailable.
- The environment natively supports step-based validation of these open-loop scripts, strictly bounded **reward signals**, and **deterministic outcomes**.

⚠️ **Training will be executed during the hackathon using provided compute resources.** 

---

## 🏗️ Architecture

```text
auto-sre/
├── openenv.yaml              # OpenEnv spec — all 10 tasks
├── app/
│   ├── main.py               # FastAPI + Gradio mount
│   ├── ui.py                 # Web terminal, Demo Mode, AI Copilot
│   └── routes/               # /reset /step /state /tasks /grader
├── engine/
│   ├── sandbox.py            # Shell interpreter + echo redirection
│   ├── filesystem.py         # UnionFS-style layered filesystem
│   ├── process_manager.py    # Mock ps/netstat/kill
│   └── security.py           # Command whitelist (df/du/free/top added)
├── grader/
│   └── health_check.py       # 10 graders — all with _safe_score()
├── tasks/
│   ├── registry.py           # TASK_REGISTRY — single source of truth
│   ├── t1_config.py → t6_oom_killer.py
│   ├── t7_cascading_meltdown.py   # 4-step cascade
│   ├── t8_memory_leak_loop.py     # crash-restart loop
│   ├── t9_dependency_chain_failure.py  # ordered restart
│   └── t10_config_secret_failure.py   # secret injection
└── scripts/
    ├── run_baseline_agent.py  # hardcoded + LLM baselines
    ├── train_grpo.py          # Unsloth GRPO — all 10 tasks
    └── multi_agent.py         # Commander→Planner→Executor→Critic
```

---

## 🔒 Reward Safety

All rewards are strictly clamped to the open interval **(0.01, 0.989)** using a single `_safe_score()` function.
Double-enforced: at grader level AND at API route level.

```text
Agent                     Auto-SRE Environment
  │                              │
  │── POST /reset ──────────────▶│  Broken state initialized (randomized PIDs/ports)
  │◀─ Observation ───────────────│  (stdout, stderr, cwd, health_status)
  │                              │
  │── POST /step ───────────────▶│  Shell command executed in sandbox
  │◀─ (obs, reward, done, info) ─│  Grader evaluates system state
  │                              │
  │      [repeat up to max_steps]│
```

### World Model

Each episode seeds a **stateful world model** into `sandbox.state`:

```python
{
  "disk_usage": 20,         # 0–100% — 100 only for disk-failure tasks (t5, t7)
  "memory_usage": 97,       # 0–100%
  "services_running": {"db": False, "app": True},
  "rogue_pid": 4242,        # deterministic per task (t2=4242, t6=5555, t7=6666, t8=7777)
  "config_valid": False,
}
```

Agent actions mutate this state. The grader reads it to compute reward.

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
`ls`, `cat`, `pwd`, `echo`, `ps`, `mv`, `kill`, `find`, `grep`, `mkdir`, `touch`,
`head`, `tail`, `systemctl`, `npm`, `cd`, `rm`, `df`, `du`, `free`, `top`, `ss`, `netstat`, `lsof`

---

## 🎯 Task Curriculum (t1–t10)

Ten tasks across three difficulty tiers. Each requires **multi-step sequential reasoning** — no single-command shortcuts.

### Difficulty Tiers

| Tier | Tasks | Theme |
|---|---|---|
| 🟢 **Easy** | t1, t2, t3 | Single-failure diagnosis + repair |
| 🟡 **Medium** | t4, t5, t6 | Adversarial + resource exhaustion |
| 🔴 **Hard** | t7, t8, t9, t10 | Cascading failures + ordering constraints |

### Full Task Table

| Task | Scenario | Steps Required | Key Challenge |
|---|---|---|---|
| `t1_config` | Config file misnamed `conf.bak` | 3+ | locate → rename → restart |
| `t2_port` | Randomized rogue process on port | 3+ | netstat → ps → kill |
| `t3_dep` | Missing npm dependencies | 4+ | inspect → cd → install → verify |
| `t4_trap` | Healthy system — alert is false | 3+ | diagnose only, no repair |
| `t5_disk_full` | Randomized log fills disk 100% | 3+ | df → find → rm |
| `t6_oom_killer` | Rogue memory hog, random PID | 3+ | free → ps → kill |
| `t7_cascading_meltdown` | Rogue logger → disk full → DB crash | 4 ordered | df → rm log → kill rogue → restart DB |
| `t8_memory_leak_loop` | Service crash-restart loop, memory at 97% | 4 ordered | free → ps → kill → restart service |
| `t9_dependency_chain_failure` | db→cache→app all down | 5 ordered | log trace → restart db → cache → app |
| `t10_config_secret_failure` | Wrong DB secret in config | 5 ordered | log → inspect → echo secret → restart |

### Deterministic State (Training-Stable)

PIDs are deterministic per task to allow stable GRPO training (agent can learn correct kill commands):
- **t2_port** — PID `4242`, port `8080`
- **t6_oom_killer** — PID `5555`
- **t7_cascading_meltdown** — PID `6666`
- **t8_memory_leak_loop** — PID `7777`

The environment state (disk%, memory%, service flags) still varies meaningfully across tasks. Multi-agent evaluation continues to require dynamic `ps aux` parsing.

---

## 🏆 Reward System

### Multi-Component Dense Rewards

Every task uses **milestone-based accumulation** — reward increases at each correct step:

```python
# Example: T7 CascadeGrader
total = 0.0
if "df" in history:           total += 0.15  # diagnosed disk
if log_cleared:               total += 0.25  # cleared logs
if rogue_dead:                total += 0.25  # killed process
if db_running:                total += 0.25  # restarted DB
```

### Reward Components

| Component | Effect |
|---|---|
| **Progress reward** | +0.10–0.25 per completed step |
| **Correctness reward** | +0.25–0.45 for key action |
| **Sequence correctness** | Out-of-order penalty (T9) |
| **Efficiency bonus** | +0.05 if solved in ≤6 steps |
| **Excessive commands** | −0.08 if >10–15 steps |
| **Invalid command** | reward=0.01, done=False |

### Strict Bounds

All rewards clamped to **(0.01, 0.989)** — never `0.0` or `1.0`:

```python
_SCORE_MIN = 0.01
_SCORE_MAX = 0.989

def _safe_score(raw: float) -> float:
    score = float(raw)
    return max(_SCORE_MIN, min(_SCORE_MAX, score))
```

This prevents the `0.0` or `1.0` boundary values that cause OpenEnv Phase 2 validation failures.

---

## 🛡️ Anti-Reward Hacking

| Protection | Mechanism |
|---|---|
| **No step skipping** | T7/T9: prerequisites enforced via state checks |
| **No fake restart** | `systemctl restart db` fails if disk full or rogue alive |
| **Randomized state** | PIDs/ports change every episode |
| **Command whitelist** | `security.py` — only safe commands allowed |
| **Max step limit** | Episode auto-terminates at `max_steps` |
| **Wrong-order penalty** | T9: restarting cache before db = −0.15 |

---


## 🚀 RL Training Pipeline

`scripts/train_grpo.py` uses **Unsloth + TRL GRPOTrainer** to fine-tune `Qwen2.5-1.5B-Instruct` across all 10 tasks.

### Training Architecture

```python
# Task selection: round-robin curriculum (easy → hard)
task_id = TASKS[episode % len(TASKS)]  # dynamically loaded

# Reward function: live environment feedback
score = run_env_episode(task_id, commands)  # hits /reset + /step + /grader
```

### Running Training (Google Colab)

```bash
!git clone https://github.com/goatedAreeeb/auto-dev-.git
%cd auto-dev-/auto-sre

!ls

# Ensure unsloth import at top
!sed -i '1s/^/import unsloth\n/' scripts/train_grpo.py

import os
os.environ["AUTO_SRE_URL"] = "https://goated1-auto-sre.hf.space"

!pip install -q unsloth trl transformers accelerate bitsandbytes httpx matplotlib


!sed -i '1s/^/import unsloth\n/' scripts/train_grpo.py

!python scripts/train_grpo.py

from google.colab import files
files.download('/content/plots/reward_curve_10ep.png')

from google.colab import files
files.download('/content/auto-dev-/auto-dev-/auto-sre/grpo_artifacts.json')

### Training Results

After training, plots are saved to `plots/` with:
- **Overall reward curve** — average reward per training step
- **Loss curve** — surrogate policy loss per step
- **Per-task bar chart** — average reward per scenario


*Reward per training step across all 10 SRE tasks — higher is better. Convergence expected after ~50 steps with corrected training loop.*
[REWARD LOG] Avg: 0.0569 | Step 15
{'loss': '0.006266', 'grad_norm': '0.2999', 'learning_rate': '9.947e-06', 'num_tokens': '4.283e+04', 'completions/mean_length': '26.84', 'completions/min_length': '8', 'completions/max_length': '134', 'completions/clipped_ratio': '0', 'completions/mean_terminated_length': '26.84', 'completions/min_terminated_length': '8', 'completions/max_terminated_length': '134', 'rewards/openenv_reward_func/mean': '0.05687', 'rewards/openenv_reward_func/std': '0.1481', 'reward': '0.05687', 'reward_std': '0.1326', 'frac_reward_zero_std': '0.25', 'completion_length': '26.84', 'kl': '0.0007383', 'clip_ratio/low_mean': '0', 'clip_ratio/low_min': '0', 'clip_ratio/high_mean': '0', 'clip_ratio/high_max': '0', 'clip_ratio/region_mean': '0', 'epoch': '0.4688'}
 16% 15/96 [22:02<1:36:54, 71.79s/it]Both `max_new_tokens` (=256) and `max_length`(=32768) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
[REWARD LOG] Avg: 0.0694 

```text
🦥 Unsloth: Will patch your computer to enable 2x faster free finetuning.
🦥 Unsloth Zoo will now patch everything to make training faster!
Unsloth: UnslothBCOTrainer is already patched.
Unsloth: UnslothCPOTrainer is already patched.
Unsloth: UnslothDPOTrainer is already patched.
Unsloth: UnslothGKDTrainer is already patched.
Unsloth: UnslothGRPOTrainer is already patched.
Unsloth: UnslothKTOTrainer is already patched.
Unsloth: UnslothNashMDTrainer is already patched.
Unsloth: UnslothOnlineDPOTrainer is already patched.
Unsloth: UnslothORPOTrainer is already patched.
Unsloth: UnslothPPOTrainer is already patched.
Unsloth: UnslothPRMTrainer is already patched.
Unsloth: UnslothRewardTrainer is already patched.
Unsloth: UnslothRLOOTrainer is already patched.
Unsloth: UnslothSFTTrainer is already patched.
Unsloth: UnslothXPOTrainer is already patched.
Initializing Unsloth RL Pipeline — 10 tasks loaded
Tasks: ['t1_config', 't2_port', 't3_dep', 't4_trap', 't5_disk_full', 't6_oom_killer', 't7_cascading_meltdown', 't8_memory_leak_loop', 't9_dependency_chain_failure', 't10_config_secret_failure']
==((====))==  Unsloth 2026.4.8: Fast Qwen2 patching. Transformers: 5.5.0.
   \\   /|    Tesla T4. Num GPUs = 1. Max memory: 14.563 GB. Platform: Linux.
O^O/ \_/ \    Torch: 2.10.0+cu128. CUDA: 7.5. CUDA Toolkit: 12.8. Triton: 3.6.0
\        /    Bfloat16 = FALSE. FA [Xformers = 0.0.35. FA2 = False]
 "-____-"     Free license: http://github.com/unslothai/unsloth
Unsloth: Fast downloading is enabled - ignore downloading bars which are red colored!
Loading weights: 100% 338/338 [00:05<00:00, 63.91it/s]
config.json: 1.58kB [00:00, 4.38MB/s]
tokenizer_config.json: 7.36kB [00:00, 16.4MB/s]
vocab.json: 2.78MB [00:00, 95.8MB/s]
merges.txt: 1.67MB [00:00, 114MB/s]
tokenizer.json: 100% 11.4M/11.4M [00:00<00:00, 18.2MB/s]
added_tokens.json: 100% 605/605 [00:00<00:00, 3.19MB/s]
special_tokens_map.json: 100% 614/614 [00:00<00:00, 2.96MB/s]
unsloth/qwen2.5-1.5b-instruct-unsloth-bnb-4bit does not have a padding token! Will use pad_token = <|PAD_TOKEN|>.
Unsloth 2026.4.8 patched 28 layers with 28 QKV layers, 28 O layers and 28 MLP layers.
Unsloth: We now expect `per_device_train_batch_size` * `gradient_accumulation_steps` * `world_size` to be a multiple of `num_generations`.
We will change the batch size of 1 to the `num_generations` of 8
warmup_ratio is deprecated and will be removed in v5.2. Use `warmup_steps` instead.
Starting GRPO Training...
The tokenizer has new PAD/BOS/EOS tokens that differ from the model config and generation config. The model config and generation config were aligned accordingly, being updated with the tokenizer's values. Updated tokens: {'bos_token_id': None}.
==((====))==  Unsloth - 2x faster free finetuning | Num GPUs used = 1
   \\   /|    Num examples = 128 | Num Epochs = 3 | Total steps = 96
O^O/ \_/ \    Batch size per device = 8 | Gradient accumulation steps = 4
\        /    Data Parallel GPUs = 1 | Total batch size (8 x 4 x 1) = 32
 "-____-"     Trainable parameters = 18,464,768 of 1,562,179,072 (1.18% trained)
```

---

** Graph Before Training***
<img width="1800" height="750" alt="image" src="https://github.com/user-attachments/assets/e057ca11-7a3b-4f1b-a467-1fee44eecdbd" />
***Graph After Training**
<img width="2084" height="732" alt="reward_curve_10ep (1)" src="https://github.com/user-attachments/assets/9ce0bc1c-3cf8-48e8-9c83-7ff95dad3e4f" />

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/reset` | Init task. Body: `{"task_id": "t1_config"}` |
| `POST` | `/step` | Run command. Body: `{"tool": "run_command", "arguments": "ls /etc/app"}` |
| `GET` | `/state` | Full sandbox state snapshot |
| `GET` | `/tasks` | All 10 task definitions |
| `GET` | `/grader?task_id=<id>` | Current grader score — validates `task_id` matches active session |
| `GET` | `/healthz` | Health check |
| `GET` | `/docs` | Swagger UI |

### Example: T9 Dependency Chain

```bash
# Reset
curl -X POST http://localhost:8000/reset -d '{"task_id": "t9_dependency_chain_failure"}'

# Trace the chain
curl -X POST http://localhost:8000/step -d '{"command": "cat /var/log/app.log"}'
# → stderr mentions cache failure

# Fix root first — wrong order is penalized!
curl -X POST http://localhost:8000/step -d '{"command": "systemctl restart db"}'
curl -X POST http://localhost:8000/step -d '{"command": "systemctl restart cache"}'
curl -X POST http://localhost:8000/step -d '{"command": "systemctl restart app"}'
# → {"reward": 0.989, "done": true}
```

---

## 🚀 Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/goatedAreeeb/auto-dev-.git
cd auto-dev-/auto-sre
```

### 2. Install dependencies
```bash
pip install -e ".[dev]"
```

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env — add OPENAI_API_KEY if you want live AI Copilot hints
```

### 4. Run locally
```bash
python -m uvicorn app.main:app --reload --port 8000
# API: http://localhost:8000
# UI:  http://localhost:8000/
```

Then open **http://localhost:8000** in your browser.

---

## 🧪 Validation

### Run all tests
```bash
pytest tests/
```

### Run the baseline agent
```bash
python scripts/run_baseline_agent.py
```

Expected output (Deterministic, state-driven rule-based agent):
```json
{
  "results": [
    {"task_id": "t1_config", "reward": 0.989, "done": true},
    {"task_id": "t2_port",   "reward": 0.989, "done": true},
    {"task_id": "t3_dep",    "reward": 0.989, "done": true},
    {"task_id": "t4_trap",   "reward": 0.989, "done": true},
    {"task_id": "t5_disk_full",  "reward": 0.989, "done": true},
    {"task_id": "t6_oom_killer", "reward": 0.989, "done": true},
    {"task_id": "t7_cascading_meltdown", "reward": 0.989, "done": true},
    {"task_id": "t8_memory_leak_loop", "reward": 0.989, "done": true},
    {"task_id": "t9_dependency_chain_failure", "reward": 0.989, "done": true},
    {"task_id": "t10_config_secret_failure", "reward": 0.989, "done": true}
  ],
  "average_reward": 0.989
}
```

### Run the Multi-Agent System
```bash
python scripts/multi_agent.py
```

Expected output (Adaptive Reasoning mode):
```json
[
  {"task_id": "t1_config", "reward": 0.97, "commands_used": 2},
  {"task_id": "t2_port", "reward": 0.75, "commands_used": 17},
  {"task_id": "t3_dep", "reward": 0.97, "commands_used": 3},
  {"task_id": "t4_trap", "reward": 0.97, "commands_used": 3},
  {"task_id": "t5_disk_full", "reward": 0.97, "commands_used": 3},
  {"task_id": "t6_oom_killer", "reward": 0.97, "commands_used": 4},
  {"task_id": "t7_cascading_meltdown", "reward": 0.97, "commands_used": 6},
  {"task_id": "t8_memory_leak_loop", "reward": 0.97, "commands_used": 5},
  {"task_id": "t9_dependency_chain_failure", "reward": 0.9, "commands_used": 6},
  {"task_id": "t10_config_secret_failure", "reward": 0.95, "commands_used": 5}
]

Average reward across all tasks: 0.9390
```

> Unlike the baseline agent which uses deterministic state-machine logic, the Multi-Agent system relies on a **Commander → Planner → Executor → Critic** hierarchy for dynamic self-correction and exploration. It achieves a **highly competitive `0.9390` average reward** across all 10 tasks, successfully demonstrating adaptive reasoning and recovery from failure states.

### Check available tasks
```bash
curl http://localhost:8000/tasks
```

---

## 🏆 OpenEnv Compliance

- ✅ **Phase 1**: STDOUT format `[STEP] ... reward=X.XX`
- ✅ **Phase 2**: All rewards strictly in `(0.01, 0.989)` — double-enforced
- ✅ All 10 tasks registered in `openenv.yaml` — synced with `TASK_REGISTRY`
- ✅ `/reset`, `/step`, `/state`, `/tasks`, `/grader`, `/healthz` all functional
- ✅ Invalid commands → `done=False`, `reward=0.01` (no crash)
- ✅ World model state mutated by actions and read by graders

---

## 🔧 Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `AUTO_SRE_URL` | No | `http://localhost:8000` | Environment URL for training/agents |
| `OPENAI_API_KEY` | No | — | Enables live AI Copilot hints in UI |
| `OPENAI_BASE_URL` | No | `https://api.openai.com/v1` | LLM proxy endpoint |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | Model for AI Copilot |
| `STEP_TIMEOUT` | No | `5` | Max seconds per sandbox command |

---

## 📜 License

MIT — see `LICENSE` for details.

---

*Built for the OpenEnv Hackathon 2026 — Real-World Infrastructure Track*
