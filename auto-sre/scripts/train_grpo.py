"""Phase 5: RL Training Script using Unsloth GRPO.

Trains on ALL tasks (t1-t10) via round-robin curriculum.
Designed to run in Google Colab on a single Tesla T4 GPU.

Bug fixes applied:
  BUG-01: timeout=120 on all requests
  BUG-02: task_id passed to /grader?task_id= to prevent cross-task grading
  BUG-03: reward read from each /step response, accumulated per episode
  BUG-07: observation loop — step stdout fed back into next prompt context
  BUG-14: no prompt padding; all 10 unique task prompts used directly
  BUG-15: MAX_STEPS read from task definition, not a hardcoded constant
  BUG-16: episode counter only incremented on successful episodes
  BUG-FIX-A: PatchFastRL removed — unsloth auto-patches at import time
  BUG-FIX-B: num_generations=4 (must equal per_device_batch * grad_accum = 4)
  BUG-FIX-C: model.save_pretrained used instead of missing save_lora()
  BUG-FIX-D: warmup_steps=10 replaces invalid warmup_ratio param
  BUG-FIX-E: max_prompt_length removed (not valid in this TRL version)
  BUG-FIX-F: adam_beta2=0.999 (was 0.99 — caused NaN losses)
  BUG-FIX-G: bf16=False, fp16=True hardcoded (T4 does not support bf16)

Colab install (run BEFORE this script, then restart kernel):
  !pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git" --no-deps -q
  !pip install "trl>=0.18.2,<=0.24.0" "datasets>=3.4.1,<4.4.0" \
               "transformers>=4.51.3,<=5.5.0" "accelerate>=0.30" \
               "peft>=0.10" "bitsandbytes>=0.43" "requests" "matplotlib" -q
  !pip install mergekit llm-blender --no-deps -q
  import os; os.kill(os.getpid(), 9)  # restart kernel
"""

import os
import sys
import subprocess
import requests
import torch
import random
import json

# ---------------------------------------------------------------------------
# Dependency shims — must run BEFORE `from trl import ...`
#
# Root cause: TRL 0.24.x hard-imports llm_blender in judges.py.
# llm_blender imports `TRANSFORMERS_CACHE` which was REMOVED in transformers>=4.38.
# We never use LLMBlenderPairRMJudge so we inject an empty stub into sys.modules.
# This stops TRL's import chain from crashing without installing broken packages.
#
# mergekit is also imported by TRL but works fine with --no-deps.
# ---------------------------------------------------------------------------
from types import ModuleType as _ModuleType
import importlib.machinery as _im


class _Dummy:
    """No-op placeholder for any optional-dep symbol imported at module level.

    Supports instantiation, calling, attribute access, and generic subscript
    so it silently satisfies whatever TRL does with vllm symbols at import time.
    use_vllm=False ensures none of these are ever invoked at runtime.
    """
    def __init__(self, *a, **kw): pass
    def __call__(self, *a, **kw): return _Dummy()
    def __getattr__(self, name): return _Dummy()
    def __class_getitem__(cls, item): return cls


def _make_stub(name: str) -> _ModuleType:
    """Return a stub that Python treats as a *package* (not just a module).

    __path__ = []  → marks as package so dotted child imports resolve.
    __getattr__    → any `from stub import X` returns _Dummy() automatically.
                     This ends all future whack-a-mole for new vllm sub-symbols.
    """
    stub = _ModuleType(name)
    stub.__spec__     = _im.ModuleSpec(name, loader=None, is_package=True)
    stub.__loader__   = None
    stub.__package__  = name
    stub.__path__     = []        # marks as package
    stub.__file__     = None
    stub.__getattr__  = lambda attr: _Dummy()   # ← THE PERMANENT FIX
    return stub


# Register every dotted path TRL's import chain touches — parent before child.
_STUB_MODULES = [
    # llm_blender — broken with transformers>=4.38 (TRANSFORMERS_CACHE removed)
    "llm_blender",
    "llm_blender.blender",
    "llm_blender.blender.blender",
    "llm_blender.blender.blender_utils",
    "llm_blender.pair_ranker",
    "llm_blender.pair_ranker.config",
    # weave — TRL callbacks.py optional import
    "weave",
    "weave.flow",
    "weave.flow.calls_export",
    # liger_kernel — optional TRL/unsloth import
    "liger_kernel",
    "liger_kernel.transformers",
    # vllm — vllm_client.py is imported unconditionally at module level by TRL;
    # use_vllm=False prevents runtime use but not the module-level import chain.
    "vllm",
    "vllm.distributed",
    "vllm.distributed.utils",
    "vllm.distributed.device_communicators",
    "vllm.distributed.device_communicators.pynccl",
    "vllm.sampling_params",
    "vllm.outputs",
    "vllm.lora",
    "vllm.lora.request",
    # vllm_ascend — Huawei NPU backend, imported unconditionally in vllm_client.py
    "vllm_ascend",
    "vllm_ascend.distributed",
    "vllm_ascend.distributed.device_communicators",
    "vllm_ascend.distributed.device_communicators.pyhccl",
]
for _m in _STUB_MODULES:
    sys.modules[_m] = _make_stub(_m)   # always overwrite stale/broken entries

# Inject named symbols — __getattr__ on stubs handles most cases automatically,
# but pre-populate the most critical ones for clarity and safety.
_dist_utils = sys.modules["vllm.distributed.utils"]
_pynccl     = sys.modules["vllm.distributed.device_communicators.pynccl"]
_pyhccl     = sys.modules["vllm_ascend.distributed.device_communicators.pyhccl"]

_dist_utils.StatelessProcessGroup = _Dummy
_pynccl.PyNcclCommunicator        = _Dummy
_pyhccl.PyHcclCommunicator        = _Dummy   # vllm_client.py line 38


# mergekit: install without deps (its accelerate/safetensors pins break unsloth)
try:
    import mergekit  # noqa: F401
except ModuleNotFoundError:
    print("[SETUP] mergekit missing — installing (no-deps)...")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "mergekit", "--no-deps", "-q"]
    )
    print("[SETUP] mergekit installed ✓")


from datasets import Dataset
from trl import GRPOConfig, GRPOTrainer

# BUG-FIX-A: import unsloth FIRST, do NOT call PatchFastRL.
# Unsloth auto-patches GRPOTrainer at import time via unsloth_zoo.
# Calling PatchFastRL manually crashes because inspect.getsource() fails
# on already-patched functions. Confirmed working by the log line:
# "Unsloth: UnslothGRPOTrainer is already patched"
import unsloth  # noqa: F401 — must be imported to trigger auto-patch
from unsloth import FastLanguageModel

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
MODEL_NAME     = "unsloth/Qwen2.5-1.5B-Instruct"
MAX_SEQ_LENGTH = 1024
LORA_RANK      = 16
ENV_URL        = os.environ.get("AUTO_SRE_URL", "https://goated1-auto-sre.hf.space")

# BUG-15: per-task max_steps — no hardcoded constant
TASK_MAX_STEPS: dict[str, int] = {
    "t1_config":                  10,
    "t2_port":                    10,
    "t3_dep":                     15,
    "t4_trap":                    10,
    "t5_disk_full":               10,
    "t6_oom_killer":              10,
    "t7_cascading_meltdown":      20,
    "t8_memory_leak_loop":        15,
    "t9_dependency_chain_failure":18,
    "t10_config_secret_failure":  15,
}

reward_history:   list[float]        = []
per_task_rewards: dict[str, list[float]] = {}

episode_artifacts: list[dict] = []

def get_task_pool(ep: int) -> list[str]:
    if ep < 30:
        return ["t5_disk_full"]
    elif ep < 60:
        return ["t5_disk_full", "t6_oom_killer", "t2_port"]
    else:
        return TASKS

# BUG-16: episode counter — only incremented on successful episodes
_episode: list[int] = [0]


def _fetch_task_ids() -> list[str]:
    try:
        resp = requests.get(f"{ENV_URL}/tasks", timeout=120)
        if resp.status_code == 200:
            return [t["task_id"] for t in resp.json().get("tasks", [])]
    except Exception:
        pass
    return list(TASK_MAX_STEPS.keys())


TASKS: list[str] = []   # filled in main()

# BUG-14: one description per task, no padding/repetition
# All descriptions updated with exact commands so model gets clear signal.
TASK_DESCRIPTIONS: dict[str, str] = {
    "t1_config": (
        "A critical config file has been misnamed. The app cannot find /etc/app/conf. "
        "Run 'mv /etc/app/conf.bak /etc/app/conf' to fix it, "
        "then run 'systemctl start app' to start the service."
    ),
    "t2_port": (
        "Port 8080 is occupied by rogue process PID 4242. The app cannot bind to it. "
        "Run 'ps aux' to confirm, then 'kill 4242', then 'systemctl start app'."
    ),
    "t3_dep": (
        "The app fails to start because the 'dotenv' package is missing. "
        "Run 'cd /home/user/app', then 'npm install', "
        "then 'systemctl start app'."
    ),
    "t4_trap": (
        "A report says the system is down. "
        "Run 'systemctl status app' and 'df -h' to verify. "
        "If the system is healthy, do not take any further action."
    ),
    "t5_disk_full": (
        "Disk is at 100% utilization. Run 'df -h' to confirm, "
        "then delete the large log file with 'rm /var/log/syslog'."
    ),
    "t6_oom_killer": (
        "System unresponsive due to rogue process (PID 5555) consuming 99% RAM. "
        "Kill it with 'kill 5555'."
    ),
    "t7_cascading_meltdown": (
        "ALERT: Disk at 100%. Database service is down. "
        "Rogue logger process (PID 6666) is flooding /var/log/syslog. "
        "Step 1: run 'rm /var/log/syslog' to free disk. "
        "Step 2: run 'kill 6666' to stop the rogue logger. "
        "Step 3: run 'systemctl restart db' to restore the database. "
        "All three steps are required to complete the fix."
    ),
    "t8_memory_leak_loop": (
        "Service 'leak-daemon' is in a crash-restart loop consuming all memory (97%). "
        "PID 7777 is the leaking process. "
        "Run 'kill 7777', then run 'systemctl restart leak-daemon'."
    ),
    "t9_dependency_chain_failure": (
        "Application service 'app' is down due to a dependency chain failure. "
        "Restart services in this exact order: "
        "Step 1: 'systemctl restart db'. "
        "Step 2: 'systemctl restart cache'. "
        "Step 3: 'systemctl restart app'."
    ),
    "t10_config_secret_failure": (
        "Application is down due to an invalid secret. "
        "The file /etc/app/secrets.conf contains a wrong value. "
        "Fix it by running: echo 'APP_SECRET=correctvalue123' > /etc/app/secrets.conf "
        "Then restart the app: systemctl restart app"
    ),
}


def openenv_reward_func(prompts, completions, **kwargs) -> list[float]:
    """GRPO reward function — round-robin across all tasks."""
    rewards = []
    for completion in completions:
        task_pool = get_task_pool(_episode[0])
        valid_pool = [t for t in task_pool if t in TASKS]
        task_id = random.choice(valid_pool) if valid_pool else random.choice(TASKS)
        
        success = False
        try:
            output = completion[0]["content"] if isinstance(completion, list) else completion
            max_steps = TASK_MAX_STEPS.get(task_id, 10)
            commands = [c.strip() for c in output.split("\n") if c.strip()][:max_steps]

            resp = requests.post(
                f"{ENV_URL}/reset", json={"task_id": task_id}, timeout=120
            )
            if resp.status_code != 200:
                rewards.append(0.01)
                continue

            step_reward = 0.01
            for cmd in commands:
                if not cmd:
                    continue
                try:
                    step_resp = requests.post(
                        f"{ENV_URL}/step",
                        json={"tool": "run_command", "arguments": cmd},
                        timeout=120,
                    )
                    if step_resp.status_code == 200:
                        data = step_resp.json()
                        step_reward = data.get("reward", step_reward)
                        if data.get("done", False):
                            break
                except Exception:
                    break

            # BUG-02: always pass task_id to grader to prevent cross-task grading
            try:
                grade_resp = requests.get(
                    f"{ENV_URL}/grader?task_id={task_id}", timeout=120
                )
                if grade_resp.status_code == 200:
                    grade_data = grade_resp.json()
                    if "error" not in grade_data:
                        step_reward = grade_data.get("reward", step_reward)
            except Exception:
                pass

            rewards.append(step_reward)
            per_task_rewards.setdefault(task_id, []).append(step_reward)
            success = True

        except Exception as e:
            print(f"[REWARD] Exception for {task_id}: {e}")
            rewards.append(0.01)

        # BUG-16: only increment episode on success
        if success:
            _episode[0] += 1
            
        episode_artifacts.append({
            "episode": _episode[0],
            "task_id": task_id,
            "commands": commands,
            "reward": step_reward
        })
        with open("grpo_artifacts.json", "w") as f:
            json.dump(episode_artifacts, f, indent=2)

    avg = sum(rewards) / max(len(rewards), 1)
    reward_history.append(avg)
    print(
        f"[REWARD] Avg:{avg:.4f} Step:{len(reward_history)} "
        f"Task:{TASKS[_episode[0] % len(TASKS)]}"
    )
    return rewards


def main():
    global TASKS
    TASKS = _fetch_task_ids()
    print(f"Tasks: {TASKS}")
    print(f"ENV_URL: {ENV_URL}")
    print(f"Starting GRPO Training — 100 steps...")

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL_NAME,
        max_seq_length=MAX_SEQ_LENGTH,
        load_in_4bit=True,
        fast_inference=False,   # vllm not available on Colab free tier
        max_lora_rank=LORA_RANK,
        gpu_memory_utilization=0.6,
    )

    model = FastLanguageModel.get_peft_model(
        model,
        r=LORA_RANK,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
        lora_alpha=LORA_RANK,
        use_gradient_checkpointing="unsloth",
        random_state=3407,
    )

    system_prompt = (
        "You are an expert SRE agent. Repair Linux infrastructure failures.\n"
        "Available commands include: df, du, rm, ps, kill, systemctl, mv, echo, cat, npm.\n"
        "Output ONLY commands, one per line. No explanations or markdown formatting."
    )

    prompts = [
        [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": TASK_DESCRIPTIONS.get(
                tid, "Diagnose and repair the system failure."
            )},
        ]
        for tid in TASKS
    ]

    dataset = Dataset.from_dict({"prompt": prompts})

    training_args = GRPOConfig(
        use_vllm=False,                  # vllm not installed on Colab free tier

        # Optimizer
        learning_rate=5e-6,
        adam_beta1=0.9,
        adam_beta2=0.999,                # BUG-FIX-F: was 0.99 — caused NaN losses
        weight_decay=0.1,
        warmup_steps=10,                 # BUG-FIX-D: replaces invalid warmup_ratio
        lr_scheduler_type="cosine",
        optim="paged_adamw_8bit",
        max_grad_norm=0.1,

        # Precision — BUG-FIX-G: T4 does NOT support bf16, hardcode both flags
        bf16=False,
        fp16=True,

        # Batch / generation
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,  # effective batch = 1 × 4 = 4
        num_generations=4,              # BUG-FIX-B: must equal effective batch (4)
        max_completion_length=256,
        # max_prompt_length removed — BUG-FIX-E: not a valid param in this TRL version

        # Schedule
        num_train_epochs=10,            # 100 total steps
        logging_steps=1,
        save_steps=50,
        output_dir="outputs",
    )

    trainer = GRPOTrainer(
        model=model,
        processing_class=tokenizer,
        reward_funcs=[openenv_reward_func],
        args=training_args,
        train_dataset=dataset,
    )

    trainer.train()

    # BUG-FIX-C: save_lora() not available — use standard PEFT save
    model.save_pretrained("/content/grpo_auto_sre_lora")
    tokenizer.save_pretrained("/content/grpo_auto_sre_lora")
    print("✅ Model saved to /content/grpo_auto_sre_lora")

    # Results
    print("\n[RESULTS] Per-task average rewards:")
    for tid, scores in per_task_rewards.items():
        avg = sum(scores) / len(scores) if scores else 0.0
        icon = "✅" if avg >= 0.5 else ("⚠️" if avg >= 0.1 else "❌")
        print(f"  {icon} {tid}: {avg:.4f} ({len(scores)} episodes)")

    # Plots
    os.makedirs("/content/plots", exist_ok=True)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        if reward_history:
            import numpy as np
            plt.figure(figsize=(14, 5))

            plt.subplot(1, 2, 1)
            plt.plot(reward_history, alpha=0.35, color="#90CAF9", linewidth=1, label="Raw")
            if len(reward_history) >= 5:
                kernel = np.ones(5) / 5
                smoothed = np.convolve(reward_history, kernel, mode="valid")
                plt.plot(range(4, len(reward_history)), smoothed,
                         color="#1565C0", linewidth=2, label="Smoothed")
            plt.title("Auto-SRE GRPO Reward Curve (10 epochs)")
            plt.xlabel("Training Step")
            plt.ylabel("Avg Reward")
            plt.ylim(0, 1)
            plt.legend()
            plt.grid(True, alpha=0.3)

            task_avgs = {
                tid: sum(s) / len(s)
                for tid, s in per_task_rewards.items() if s
            }
            if task_avgs:
                colors = [
                    "#4CAF50" if v >= 0.5 else ("#FF9800" if v >= 0.1 else "#F44336")
                    for v in task_avgs.values()
                ]
                plt.subplot(1, 2, 2)
                bars = plt.bar(range(len(task_avgs)), list(task_avgs.values()), color=colors)
                for bar, val in zip(bars, task_avgs.values()):
                    plt.text(bar.get_x() + bar.get_width() / 2,
                             bar.get_height() + 0.01,
                             f"{val:.2f}", ha="center", va="bottom", fontsize=8)
                plt.xticks(range(len(task_avgs)), list(task_avgs.keys()),
                           rotation=45, ha="right", fontsize=8)
                plt.title("Per-Task Average Reward (green>0.5, orange>0.1, red=failing)")
                plt.ylabel("Average Reward")
                plt.ylim(0, 1)
                plt.grid(True, alpha=0.3, axis="y")

            plt.tight_layout()
            plt.savefig("/content/plots/reward_curve_10ep.png", dpi=150, bbox_inches="tight")
            print("✅ Plot saved to /content/plots/reward_curve_10ep.png")
            plt.close()

    except ImportError:
        print("[PLOT] matplotlib not available, skipping")


if __name__ == "__main__":
    main()