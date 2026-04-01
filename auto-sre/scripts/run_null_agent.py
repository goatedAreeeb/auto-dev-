"""Null Agent — sends random whitelisted commands to stress-test the environment."""

import random
import httpx

BASE_URL = "http://localhost:8000"
TASKS = ["t1_config", "t2_port", "t3_dep"]
RANDOM_COMMANDS = [
    "ls /",
    "ls /etc",
    "ls /home/user",
    "cat /etc/hostname",
    "pwd",
    "echo hello",
    "ps aux",
    "find /home",
    "grep test /etc/hostname",
    "mkdir /tmp/test",
    "touch /tmp/foo.txt",
    "head /etc/hostname",
    "tail /etc/hostname",
    "systemctl status nginx",
]

NUM_STEPS = 100


def run_null_agent() -> None:
    """Run a null agent sending random commands for crash testing."""
    client = httpx.Client(base_url=BASE_URL, timeout=10.0)

    for task_id in TASKS:
        print(f"\n{'='*60}")
        print(f"Testing task: {task_id}")
        print(f"{'='*60}")

        resp = client.post("/reset", json={"task_id": task_id})
        assert resp.status_code == 200, f"Reset failed: {resp.text}"

        for step in range(NUM_STEPS):
            cmd = random.choice(RANDOM_COMMANDS)
            try:
                resp = client.post(
                    "/step",
                    json={"tool": "run_command", "arguments": cmd},
                )
                if resp.status_code == 400 and "done" in resp.text.lower():
                    print(f"  Episode ended at step {step + 1}")
                    break
                assert resp.status_code in (200, 400, 408), (
                    f"Unexpected status {resp.status_code}: {resp.text}"
                )
            except Exception as e:
                print(f"  CRASH at step {step + 1}: {e}")
                raise

        print(f"  [PASS] Completed {task_id} without crashes")

    print(f"\n{'='*60}")
    print("NULL AGENT: ALL TASKS PASSED — no crashes detected.")
    print(f"{'='*60}")


if __name__ == "__main__":
    run_null_agent()
