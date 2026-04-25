"""Scenario 6: Rogue process leaking memory until OOM.

Goal: Identify the rogue memory_hog process (PID 5555) and kill it.
"""

from __future__ import annotations

from engine.filesystem import MockFile, MockFilesystem
from engine.process_manager import MockProcess, ProcessManager
from grader.health_check import OOMGrader

TASK_ID = "t6_oom_killer"
DESCRIPTION = (
    "System unresponsive due to rogue process consuming 99% RAM. "
    "Run 'ps aux' to identify it (PID visible in output), kill it."
)
MAX_STEPS = 10

# Deterministic PID — BUG-06 fix
ROGUE_PID = 5555

GRADER = OOMGrader()


def build_initial_state() -> tuple:
    """Construct the initial mock state."""
    fs = MockFilesystem()
    pm = ProcessManager()

    fs.set_base({
        "/bin/bash": MockFile("/bin/bash", "binary", "rwxr-xr-x"),
        "/usr/bin/python3": MockFile("/usr/bin/python3", "binary", "rwxr-xr-x"),
    })
    fs.set_overlay({
        "/home/user/.bashrc": MockFile("/home/user/.bashrc", "alias ll='ls -l'"),
        "/tmp/memory_hog.py": MockFile("/tmp/memory_hog.py", "while True: leak.append('M' * 1024 * 1024)"),
    })

    pm.load([
        MockProcess(pid=1, command="init", port_bindings=[]),
        MockProcess(pid=ROGUE_PID, command="python3 /tmp/memory_hog.py", port_bindings=[]),
    ])

    state_hint = {
        "disk_usage": 20,
        "memory_usage": 99,
        "rogue_pid": ROGUE_PID,
    }
    return fs, pm, state_hint
