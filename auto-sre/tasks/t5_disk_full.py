"""Scenario 5: Disk full due to massive log file.

Goal: Identify the large file /var/log/syslog and delete it.
"""

from __future__ import annotations

from engine.filesystem import MockFile, MockFilesystem
from engine.process_manager import ProcessManager
from grader.health_check import DiskGrader

TASK_ID = "t5_disk_full"
DESCRIPTION = "System unresponsive due to 100% disk utilization. Fix it."
MAX_STEPS = 10

GRADER = DiskGrader()


def build_initial_state() -> tuple:
    """Construct the initial mock state."""
    fs = MockFilesystem()
    pm = ProcessManager()

    target_log = "/var/log/syslog"

    fs.set_base({
        "/bin/bash": MockFile("/bin/bash", "binary", "rwxr-xr-x"),
        "/usr/bin/ls": MockFile("/usr/bin/ls", "binary", "rwxr-xr-x"),
    })
    fs.set_overlay({
        "/home/user/.bashrc": MockFile("/home/user/.bashrc", "alias ll='ls -l'"),
        target_log: MockFile(target_log, "LARGE_LOG_CONTENT" * 1000000),
    })

    state_hint = {
        "disk_usage": 100,   # only this task sets 100 (BUG-08 fix)
        "target_log": target_log,
    }
    return fs, pm, state_hint
