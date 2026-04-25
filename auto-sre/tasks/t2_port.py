"""Task t2_port — port 8080 occupied scenario."""

from engine.filesystem import MockFile, MockFilesystem
from engine.process_manager import MockProcess, ProcessManager
from grader.health_check import PortGrader

TASK_ID = "t2_port"
DESCRIPTION = (
    "Port 8080 is occupied by a rogue process (PID 4242). The app cannot bind to it. "
    "Run 'ps aux' to confirm, kill PID 4242, then run 'systemctl start app' to restore service."
)
MAX_STEPS = 10

# Deterministic PID — visible in ps aux, no randomization needed (BUG-06 fix)
ROGUE_PID = 4242
TARGET_PORT = 8080


def build_initial_state() -> tuple:
    """Create the broken baseline state for this task."""
    fs = MockFilesystem()
    fs.set_base({
        "/etc/hostname": MockFile(path="/etc/hostname", content="auto-sre-host"),
        "/var/log/syslog": MockFile(path="/var/log/syslog", content="system boot ok\n"),
    })
    fs.set_overlay({
        "/home/user/app.js": MockFile(
            path="/home/user/app.js",
            content=f"const http = require('http');\nhttp.createServer().listen({TARGET_PORT});\n",
        ),
    })
    pm = ProcessManager()
    pm.load([
        MockProcess(pid=1, command="init", port_bindings=[]),
        MockProcess(pid=200, command="nginx", port_bindings=[80]),
        MockProcess(pid=ROGUE_PID, command="rogue-server", port_bindings=[TARGET_PORT]),
    ])
    state_hint = {
        "disk_usage": 20,
        "ports": {str(TARGET_PORT): ROGUE_PID},
        "target_port": TARGET_PORT,
        "rogue_pid": ROGUE_PID,
    }
    return fs, pm, state_hint


GRADER = PortGrader()
