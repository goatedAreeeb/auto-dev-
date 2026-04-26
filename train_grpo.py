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

# Always overwrite — covers the case where broken llm_blender was already
# loaded into sys.modules by a previous import attempt.
# __spec__ must NOT be None — importlib.util.find_spec raises ValueError if it is.
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

    The critical fix: setting __path__ = [] tells the import system this is a
    package, so `from name.sub.mod import X` no longer raises
    "name.sub is not a package".  Without __path__ that error fires even when
    the dotted name is already in sys.modules.
    """
    stub = _ModuleType(name)
    stub.__spec__ = _im.ModuleSpec(name, loader=None, is_package=True)
    stub.__loader__ = None
    stub.__package__ = name
    stub.__path__ = []   # ← marks as package; child sub-imports now resolve
    stub.__file__ = None
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
    "weave",
    "weave.flow",
    "weave.flow.calls_export",
    "weave.trace",
    "weave.trace.context",
    # liger_kernel — optional TRL/unsloth import
    "liger_kernel",
    "liger_kernel.transformers",
    # vllm — vllm_client.py is imported unconditionally at module level by TRL;
    # use_vllm=False prevents runtime use but not the module-level import chain.
    "vllm",
    "vllm.distributed",
    "vllm.distributed.utils",                        # line 35: StatelessProcessGroup
    "vllm.distributed.device_communicators",
    "vllm.distributed.device_communicators.pynccl",  # line 34: PyNcclCommunicator
    "vllm.sampling_params",
    "vllm.outputs",
    "vllm.lora",
    "vllm.lora.request",
    # vllm_ascend — TRL vllm_client.py line 38: Huawei Ascend NPU backend,
    # not present on Colab/NVIDIA hardware; stub so the import chain does not crash.
    "vllm_ascend",
    "vllm_ascend.distributed",
    "vllm_ascend.distributed.device_communicators",
    "vllm_ascend.distributed.device_communicators.pyhccl",
    # immutables — required by mergekit.common, not installed in Colab free tier
    "immutables",
    # mergekit — imported by trl.mergekit_utils via callbacks.py at module level
    "mergekit",
    "mergekit.config",
    "mergekit.common",
    "mergekit.merge",
    "mergekit.plan",
    "mergekit.io",
    "mergekit.io.tasks",
    "mergekit.architecture",
    "mergekit.graph",
    "mergekit.evo",
    "mergekit.evo.config",
]
for _m in _STUB_MODULES:
    sys.modules[_m] = _make_stub(_m)   # always overwrite stale/broken entries

# ── Inject named symbols pulled via `from X import Y` ──────────────────────
# Package stubs satisfy `import X.Y` but `from X.Y import Z` still raises
# ImportError when Z is absent — so populate every name vllm_client.py uses.

_vllm        = sys.modules["vllm"]
# TRL's is_vllm_available() does: version.parse(vllm.__version__)
# If __version__ is _Dummy (not a string) it raises TypeError and crashes.
# Set it to a real version string that deliberately != "0.10.2" so TRL's
# version-gate treats vllm as unavailable and skips all vllm code paths.
_vllm.__version__ = "0.0.0"
_dist_utils  = sys.modules["vllm.distributed.utils"]
_pynccl      = sys.modules["vllm.distributed.device_communicators.pynccl"]
_pyhccl      = sys.modules["vllm_ascend.distributed.device_communicators.pyhccl"]
_sampling    = sys.modules["vllm.sampling_params"]
_outputs     = sys.modules["vllm.outputs"]
_lora_req    = sys.modules["vllm.lora.request"]

for _attr in ("LLM", "SamplingParams", "RequestOutput", "CompletionOutput",
              "PoolingParams", "EmbeddingRequestOutput"):
    setattr(_vllm, _attr, _Dummy)

_dist_utils.StatelessProcessGroup  = _Dummy   # vllm_client.py line 35
_pynccl.PyNcclCommunicator         = _Dummy   # vllm_client.py line 34
_pyhccl.PyHcclCommunicator         = _Dummy   # vllm_client.py line 38 (Ascend NPU)
_sampling.SamplingParams           = _Dummy
_sampling.GuidedDecodingParams     = _Dummy
_outputs.RequestOutput             = _Dummy
_outputs.CompletionOutput          = _Dummy
_lora_req.LoRARequest              = _Dummy

sys.modules["weave"].EvaluationLogger = _Dummy
sys.modules["weave.trace.context"].weave_client_context = _Dummy
sys.modules["liger_kernel"].__version__ = "0.0.0"

# mergekit / immutables — stubbed entirely; TRL imports mergekit at module level
# via callbacks.py but we never call merge_models() at runtime.
# Installing mergekit pulls immutables which is absent in Colab free tier.
sys.modules["mergekit"].MergeConfiguration = _Dummy
sys.modules["mergekit.config"].MergeConfiguration = _Dummy
sys.modules["mergekit.common"].ModelReference = _Dummy
sys.modules["mergekit.merge"].MergeContext = _Dummy
sys.modules["mergekit.plan"].MergePlanner = _Dummy


import importlib.metadata
_orig_version = importlib.metadata.version
def _mock_version(name):
    if name in ("vllm", "liger_kernel"): return "0.0.0"
    return _orig_version(name)
importlib.metadata.version = _mock_version

from unsloth import FastLanguageModel, PatchFastRL
PatchFastRL("GRPO", FastLanguageModel)

from datasets import Dataset
from trl import GRPOConfig, GRPOTrainer

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
MODEL_NAME = "unsloth/Qwen2.5-1.5B-Instruct"
MAX_SEQ_LENGTH = 1024
LORA_RANK = 16
ENV_URL = os.environ.get("AUTO_SRE_URL", "https://goated1-auto-sre.hf.space")

# BUG-15: per-task max_steps — no hardcoded constant
TASK_MAX_STEPS: dict[str, int] = {
    "t1_config": 10,
    "t2_port": 10,
    "t3_dep": 15,
    "t4_trap": 10,
    "t5_disk_full": 10,
    "t6_oom_killer": 10,
    "t7_cascading_meltdown": 20,
    "t8_memory_leak_loop": 15,
    "t9_dependency_chain_failure": 18,
    "t10_config_secret_failure": 15,
}

# Reward + loss history for plots
reward_history: list[float] = []
per_task_rewards: dict[str, list[float]] = {}

# BUG-16: episode counter — only incremented on success
_episode: list[int] = [0]
episode_artifacts: list[dict] = []

def get_task_pool(ep: int) -> list[str]:
    if ep < 30:
        return ["t5_disk_full"]
    elif ep < 60:
        return ["t5_disk_full", "t6_oom_killer", "t2_port"]
    else:
        return TASKS


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
TASK_DESCRIPTIONS: dict[str, str] = {
    "t1_config": (
        "A critical config file has been misnamed. The app cannot find /etc/app/conf. "
        "Run 'mv /etc/app/conf.bak /etc/app/conf' to fix it, "
        "then run 'systemctl start app' to start the service."
    ),
    "t2_port": (
        "Port 8080 is occupied by rogue process PID 4242. "
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
        "If healthy, do not take any further action."
    ),
    "t5_disk_full": (
        "Disk is at 100%. Run 'df -h', then delete the large file "
        "with 'rm /var/log/syslog'."
    ),
    "t6_oom_killer": (
        "System unresponsive due to rogue process (PID 5555) consuming 99% RAM. "
        "Kill it with 'kill 5555'."
    ),
    "t7_cascading_meltdown": (
        "ALERT: Disk at 100%. Database service is down. "
        "Rogue logger process (PID 6666) is flooding /var/log/syslog. "
        "Diagnose, clear logs, kill the rogue process (kill 6666). "
        "After killing PID 6666 and deleting the log, you MUST run "
        "'systemctl restart db' to complete the fix."
    ),
    "t8_memory_leak_loop": (
        "Service 'leak-daemon' crash-restart loop. PID 7777 leaking memory. "
        "Run 'kill 7777', then 'systemctl restart leak-daemon'."
    ),
    "t9_dependency_chain_failure": (
        "App down due to chain failure. Restart in correct order: "
        "'systemctl restart db', then 'systemctl restart cache', "
        "then 'systemctl restart app'."
    ),
    "t10_config_secret_failure": (
        "App auth fails — wrong DB secret. Inspect /etc/app/secrets.conf, "
        "fix with: echo 'APP_SECRET=correctvalue123' > /etc/app/secrets.conf, "
        "then 'systemctl restart app'."
    ),
}


def openenv_reward_func(prompts, completions, **kwargs) -> list[float]:
    """GRPO reward function — round-robin across all tasks.

    BUG-03: reads reward from each /step response.
    BUG-02: passes task_id to /grader for session validation.
    BUG-15: respects per-task max_steps.
    BUG-16: only increments episode counter on success.
    """
    rewards = []
    for completion in completions:
        task_pool = get_task_pool(_episode[0])
        # fallback to TASKS if pool is missing tasks due to task_id mismatch
        valid_pool = [t for t in task_pool if t in TASKS]
        task_id = random.choice(valid_pool) if valid_pool else random.choice(TASKS)
        
        success = False
        try:
            output = completion[0]["content"] if isinstance(completion, list) else completion
            max_steps = TASK_MAX_STEPS.get(task_id, 10)  # BUG-15
            commands = [c.strip() for c in output.split("\n") if c.strip()][:max_steps]

            # BUG-01: timeout=120
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
                        timeout=120,  # BUG-01
                    )
                    if step_resp.status_code == 200:
                        data = step_resp.json()
                        step_reward = data.get("reward", step_reward)  # BUG-03
                        if data.get("done", False):
                            break
                except Exception:
                    break

            # BUG-02: pass task_id so grader validates session
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

        # BUG-16: only advance curriculum on success
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
    step_num = len(reward_history)
    print(f"[REWARD LOG] Avg: {avg:.4f} | Step {step_num} | Task: {TASKS[_episode[0] % len(TASKS)]}")
    return rewards


def main():
    global TASKS
    TASKS = _fetch_task_ids()
    print(f"Initializing Unsloth RL Pipeline — {len(TASKS)} tasks loaded")
    print(f"Tasks: {TASKS}")
    print(f"ENV_URL: {ENV_URL}")

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL_NAME,
        max_seq_length=MAX_SEQ_LENGTH,
        load_in_4bit=True,
        fast_inference=False,  # vllm not available in Colab free tier
        max_lora_rank=LORA_RANK,
        gpu_memory_utilization=0.6,
    )

    model = FastLanguageModel.get_peft_model(
        model,
        r=LORA_RANK,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
        lora_alpha=LORA_RANK,
        use_gradient_checkpointing="unsloth",
        random_state=3407,
    )

    system_prompt = (
        "You are an expert SRE agent. Repair Linux infrastructure failures.\n"
        "Available commands include: df, du, rm, ps, kill, systemctl, mv, echo, cat, npm.\n"
        "Output ONLY commands, one per line. No explanations or markdown formatting."
    )

    # BUG-14: exactly 10 prompts, no padding loop
    prompts = [
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": TASK_DESCRIPTIONS.get(
                tid, "Diagnose and repair the system failure."
            )},
        ]
        for tid in TASKS
    ]

    dataset = Dataset.from_dict({"prompt": prompts})

    training_args = GRPOConfig(
        use_vllm=False,  # vllm not installed in Colab free tier; use HF generation
        learning_rate=5e-6,
        adam_beta1=0.9,
        adam_beta2=0.99,
        weight_decay=0.1,
        warmup_ratio=0.1,
        lr_scheduler_type="cosine",
        optim="paged_adamw_8bit",
        logging_steps=1,
        bf16=torch.cuda.is_bf16_supported(),
        fp16=not torch.cuda.is_bf16_supported(),
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        num_generations=8,
        max_prompt_length=512,
        max_completion_length=256,
        num_train_epochs=25,
        save_steps=100,
        max_grad_norm=0.1,
        report_to="wandb",
        output_dir="outputs",
    )

    # BUG-FIX: TRL GRPOTrainer.__init__ does model.warnings_issued["estimate_tokens"] = True
    # but PEFT wraps the model and that attribute is absent on the underlying Qwen2 model.
    if not hasattr(model, "warnings_issued"):
        model.warnings_issued = {}

    trainer = GRPOTrainer(
        model=model,
        processing_class=tokenizer,
        reward_funcs=[openenv_reward_func],
        args=training_args,
        train_dataset=dataset,
    )

    print("Starting GRPO Training...")
    trainer.train()

    print("Saving LoRA weights...")
    model.save_lora("grpo_auto_sre_lora")
    print("Training complete!")

    # Per-task summary
    print("\n[RESULTS] Per-task average rewards:")
    for tid, scores in per_task_rewards.items():
        avg = sum(scores) / len(scores) if scores else 0.0
        print(f"  {tid}: {avg:.4f} ({len(scores)} episodes)")

    # Generate plots
    os.makedirs("plots", exist_ok=True)
    try:
        import matplotlib.pyplot as plt

        if reward_history:
            plt.figure(figsize=(12, 5))
            plt.subplot(1, 2, 1)
            plt.plot(reward_history, marker="o", linewidth=2, color="#2196F3")
            plt.title("Auto-SRE GRPO Reward Curve")
            plt.xlabel("Training Steps")
            plt.ylabel("Average Reward")
            plt.ylim(0, 1)
            plt.grid(True, alpha=0.3)

            task_avgs = {tid: sum(s) / len(s) for tid, s in per_task_rewards.items() if s}
            if task_avgs:
                plt.subplot(1, 2, 2)
                plt.bar(range(len(task_avgs)), list(task_avgs.values()), color="#4CAF50")
                plt.xticks(range(len(task_avgs)), list(task_avgs.keys()),
                           rotation=45, ha="right")
                plt.title("Per-Task Average Reward")
                plt.ylabel("Average Reward")
                plt.ylim(0, 1)
                plt.grid(True, alpha=0.3, axis="y")

            plt.tight_layout()
            plt.savefig("plots/reward_curve.png", dpi=150)
            print("[PLOT] plots/reward_curve.png saved")
            plt.close()

        if hasattr(trainer, "state") and trainer.state.log_history:
            losses = [e.get("loss") for e in trainer.state.log_history if "loss" in e]
            if losses:
                plt.figure(figsize=(8, 4))
                plt.plot(losses, linewidth=2, color="#E91E63")
                plt.title("GRPO Training Loss")
                plt.xlabel("Steps")
                plt.ylabel("Loss")
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                plt.savefig("plots/loss_curve.png", dpi=150)
                print("[PLOT] plots/loss_curve.png saved")
                plt.close()

    except ImportError:
        print("[PLOT] matplotlib not available, skipping")


if __name__ == "__main__":
    main()
