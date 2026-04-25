"""Task t7_cascading_meltdown — enterprise cascade failure scenario.

Scenario:
  Rogue logger (PID 6666) floods /var/log/syslog → disk at 100% → DB crashes.

Agent must (in order):
  1. df -h — detect disk full
  2. rm /var/log/syslog — free disk
  3. ps aux / kill 6666 — kill rogue logger
  4. systemctl restart db — restore database
"""

from __future__ import annotations

from engine.filesystem import MockFile, MockFilesystem
from engine.process_manager import MockProcess, ProcessManager
from grader.health_check import CascadeGrader

TASK_ID = "t7_cascading_meltdown"
DESCRIPTION = (
    "ALERT: Disk at 100%. Database service is down. "
    "Rogue logger process (PID 6666) is flooding /var/log/syslog. "
    "Diagnose, clear logs, kill the rogue process (kill 6666), and restore the DB."
)
MAX_STEPS = 20

# Deterministic PID — BUG-06 fix
ROGUE_PID = 6666

GRADER = CascadeGrader()


def build_initial_state() -> tuple:
    """Build the cascading meltdown initial state."""
    fs = MockFilesystem()

    syslog_content = (
        f"[ERROR] rogue-logger[{ROGUE_PID}]: FATAL loop iteration 1\n"
        f"[ERROR] rogue-logger[{ROGUE_PID}]: FATAL loop iteration 2\n"
        f"[ERROR] rogue-logger[{ROGUE_PID}]: FATAL loop iteration 3\n"
        "... (17GB of repeated errors) ...\n"
        f"[ERROR] rogue-logger[{ROGUE_PID}]: FATAL loop iteration 999999\n"
    )

    fs.set_base({
        "/etc/hostname": MockFile(path="/etc/hostname", content="auto-sre-host"),
        "/etc/os-release": MockFile(path="/etc/os-release", content="NAME=Ubuntu\nVERSION=22.04"),
        "/bin/bash": MockFile(path="/bin/bash", content="binary", permissions="rwxr-xr-x"),
    })
    fs.set_overlay({
        "/var/log/syslog": MockFile(path="/var/log/syslog", content=syslog_content),
        "/etc/db/db.conf": MockFile(path="/etc/db/db.conf", content="port=5432\nmax_connections=100\n"),
        "/home/user/README.md": MockFile(
            path="/home/user/README.md",
            content="# Cascading Meltdown\n\nSomething caused the disk to fill up.\nThe DB service is down. Figure it out.\n",
        ),
    })

    pm = ProcessManager()
    pm.load([
        MockProcess(pid=1, command="init", port_bindings=[]),
        MockProcess(pid=200, command="nginx", port_bindings=[80]),
        MockProcess(pid=ROGUE_PID, command="rogue-logger --infinite", port_bindings=[]),
    ])

    state_hint = {
        "disk_usage": 100,
        "memory_usage": 25,
        "ports": {"80": 200},
        "config_valid": False,
        "services_running": {"nginx": True, "db": False},
        "rogue_pid": ROGUE_PID,
        "target_log": "/var/log/syslog",
        "target_port": 80,
    }
    return fs, pm, state_hint
