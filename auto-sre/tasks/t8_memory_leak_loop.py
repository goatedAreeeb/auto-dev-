"""t8_memory_leak_loop — service stuck in crash/restart loop due to memory leak.

4-step remediation:
  1. free/top -> detect memory exhaustion
  2. ps aux -> identify leaking process (PID 7777) + crash loop (leak-daemon)
  3. kill 7777 -> stop crash loop
  4. systemctl restart leak-daemon -> restore stable service
"""
from __future__ import annotations
from engine.filesystem import MockFile, MockFilesystem
from engine.process_manager import MockProcess, ProcessManager
from grader.health_check import MemLeakGrader

TASK_ID = "t8_memory_leak_loop"
DESCRIPTION = (
    "ALERT: Service 'leak-daemon' is in a crash-restart loop consuming all memory. "
    "Memory at 97%. Run 'ps aux' to find the leaking process (PID 7777), "
    "kill it, then run 'systemctl restart leak-daemon' to restore the service."
)
MAX_STEPS = 15

# Deterministic PID — BUG-06 fix
ROGUE_PID = 7777

_state_hint: dict = {}


def build_initial_state() -> tuple:
    rogue_pid = ROGUE_PID
    fs = MockFilesystem()
    fs.set_base({
        "/etc/hostname": MockFile("/etc/hostname", "auto-sre-host"),
        "/etc/leak-daemon/config.ini": MockFile("/etc/leak-daemon/config.ini",
            "[service]\nbuffer_size=UNLIMITED\n"),
        "/var/log/leak-daemon.log": MockFile("/var/log/leak-daemon.log",
            f"[WARN] leak-daemon[{rogue_pid}]: heap growing unbounded\n"
            f"[ERROR] leak-daemon[{rogue_pid}]: OOM signal received — restarting\n"
            f"[WARN] leak-daemon[{rogue_pid}]: heap growing unbounded\n"
            "[ERROR] systemd: leak-daemon.service: Start request repeated too quickly\n"),
    })
    fs.set_overlay({
        "/home/user/status.txt": MockFile("/home/user/status.txt",
            "System health: CRITICAL\nleak-daemon: restart loop\n"),
    })
    pm = ProcessManager()
    pm.load([
        MockProcess(pid=1, command="init", port_bindings=[]),
        MockProcess(pid=200, command="nginx", port_bindings=[80]),
        MockProcess(pid=rogue_pid, command="leak-daemon --no-limit", port_bindings=[]),
    ])
    state_hint = {
        "disk_usage": 30,
        "memory_usage": 97,
        "services_running": {"nginx": True, "leak-daemon": False},
        "rogue_pid": rogue_pid,
        "target_log": "/var/log/leak-daemon.log",
        "target_port": 80,
    }
    return fs, pm, state_hint


GRADER = MemLeakGrader()
