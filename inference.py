#!/usr/bin/env python3
"""
OpenEnv Mandatory Inference Script - Auto-SRE
===================================
Enforces the mandatory STDOUT format and environment variable conventions.
"""

import os
import sys
import json
import httpx
from openai import OpenAI
from typing import List, Optional

# --- Mandatory Environment Variables ---
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
HF_TOKEN = os.getenv("HF_TOKEN")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")
AUTO_SRE_URL = os.getenv("AUTO_SRE_URL", "http://localhost:8000")

BENCHMARK = "auto-sre"
MAX_STEPS = 10

# --- Helper Functions for Mandatory STDOUT Format ---
def log_start(task: str, env: str, model: str) -> None:
    print(f"START: task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"STEP: step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )

def log_end(success: bool, steps: int, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"END: success={str(success).lower()} steps={steps} rewards={rewards_str}", flush=True)

# --- Agent System Prompt & Hints ---
SYSTEM_PROMPT = """You are an expert Site Reliability Engineer (SRE).
Your goal is to repair the broken Linux environment using CLI tools.
Respond with ONLY a single shell command. No markdown, no prefixes."""

TASK_HINTS = {
    "t1_config": "A config file is misnamed. Find and rename it to /etc/app/conf.",
    "t2_port": "Port 8080 is blocked by a rogue process. Kill it.",
    "t3_dep": "The Node.js app is missing dependencies. Run npm install.",
    "t4_trap": "A system report suggests a failure... Verify before taking action.",
}

HARDCODED_SOLUTIONS = {
    "t1_config": ["mv /etc/app/conf.bak /etc/app/conf"],
    "t2_port": ["kill -9 512"],
    "t3_dep": ["cd /home/user/app", "npm install"],
    "t4_trap": ["ls /etc/app"],
}

def run_episode(task_id: str, task_desc: str):
    # Determine if we should use LLM or Hardcoded
    use_llm = bool(HF_TOKEN and MODEL_NAME)
    model_display = MODEL_NAME if use_llm else "hardcoded"
    
    log_start(task=task_id, env=BENCHMARK, model=model_display)
    
    rewards = []
    success = False
    step_num = 0

    with httpx.Client(timeout=30.0) as client:
        # 1. Reset (using the -d '{}' pattern from the validator)
        try:
            resp = client.post(f"{AUTO_SRE_URL}/reset", json={"task_id": task_id})
            if resp.status_code != 200:
                log_end(success=False, steps=0, rewards=[0.0])
                return
        except Exception:
            log_end(success=False, steps=0, rewards=[0.0])
            return

        if use_llm:
            client_ai = OpenAI(api_key=HF_TOKEN, base_url=API_BASE_URL)
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Task: {task_desc}\nHint: {TASK_HINTS.get(task_id, '')}\nBegin."},
            ]

            for s in range(1, MAX_STEPS + 1):
                try:
                    completion = client_ai.chat.completions.create(model=MODEL_NAME, messages=messages, max_tokens=64)
                    action_str = completion.choices[0].message.content.strip()
                    
                    step_resp = client.post(f"{AUTO_SRE_URL}/step", json={"tool": "run_command", "arguments": action_str})
                    if step_resp.status_code != 200:
                        log_step(step=s, action=action_str, reward=0.0, done=True, error=step_resp.text)
                        break
                    
                    data = step_resp.json()
                    reward = data.get("reward", 0.0)
                    done = data.get("done", False)
                    obs = data.get("observation", {}).get("stdout", "") or data.get("observation", {}).get("stderr", "")
                    
                    rewards.append(reward)
                    log_step(step=s, action=action_str, reward=reward, done=done, error=None)
                    
                    if done:
                        success = (reward >= 1.0)
                        break
                    
                    messages.append({"role": "assistant", "content": action_str})
                    messages.append({"role": "user", "content": f"Output:\n{obs}"})
                except Exception as e:
                    log_step(step=s, action="error", reward=0.0, done=True, error=str(e))
                    break
        else:
            # Fallback to deterministic baseline
            commands = HARDCODED_SOLUTIONS.get(task_id, [])
            for s, action_str in enumerate(commands, 1):
                try:
                    step_resp = client.post(f"{AUTO_SRE_URL}/step", json={"tool": "run_command", "arguments": action_str})
                    data = step_resp.json()
                    reward = data.get("reward", 0.0)
                    done = data.get("done", False)
                    rewards.append(reward)
                    log_step(step=s, action=action_str, reward=reward, done=done, error=None)
                    if done:
                        success = (reward >= 1.0)
                        break
                except Exception:
                    break

    log_end(success=success, steps=len(rewards), rewards=rewards)

def main():
    try:
        resp = httpx.get(f"{AUTO_SRE_URL}/tasks", timeout=5.0)
        tasks = resp.json()["tasks"]
    except:
        tasks = [{"task_id": "t1_config", "description": "Fix configuration"}]

    for task in tasks:
        run_episode(task["task_id"], task["description"])

if __name__ == "__main__":
    main()
