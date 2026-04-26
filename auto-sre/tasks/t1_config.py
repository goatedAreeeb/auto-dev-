"""Task t1_config — misnamed config file scenario."""

from engine.filesystem import MockFile, MockFilesystem
from engine.process_manager import MockProcess, ProcessManager
from grader.health_check import ConfigGrader

TASK_ID = "t1_config"
DESCRIPTION = (
    "A critical config file has been misnamed. The app cannot find /etc/app/conf. "
    "Run 'mv /etc/app/conf.bak /etc/app/conf' to fix it, "
    "then run 'systemctl start app' to start the service."
)
MAX_STEPS = 10


def build_initial_state() -> tuple:
    """Create the broken baseline state for this task."""
    fs = MockFilesystem()
    fs.set_base({
        "/etc/hostname": MockFile(path="/etc/hostname", content="auto-sre-host"),
        "/etc/os-release": MockFile(path="/etc/os-release", content="NAME=Ubuntu\nVERSION=22.04"),
        "/var/log/syslog": MockFile(path="/var/log/syslog", content="system boot ok\n"),
    })
    fs.set_overlay({
        "/etc/app/conf.bak": MockFile(path="/etc/app/conf.bak", content="DB_HOST=localhost\nPORT=3000\n"),
        "/home/user/README.md": MockFile(path="/home/user/README.md", content="# My App\nRun with: node app.js\n"),
    })
    pm = ProcessManager()
    pm.load([
        MockProcess(pid=1, command="init", port_bindings=[]),
        MockProcess(pid=200, command="nginx", port_bindings=[80]),
    ])
    state_hint = {
        "disk_usage": 20,
        "config_valid": False,
        "services_running": {"app": False, "nginx": True},
    }
    return fs, pm, state_hint


GRADER = ConfigGrader()
