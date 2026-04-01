"""Concrete graders for each MVP task."""

from __future__ import annotations

from engine.filesystem import MockFilesystem
from engine.process_manager import ProcessManager
from grader.base import BaseGrader


class ConfigGrader(BaseGrader):
    """Grader for t1_config — misnamed config file."""

    def grade(
        self,
        filesystem: MockFilesystem,
        process_manager: ProcessManager,
        command_history: list[str],
    ) -> tuple[float, bool, str]:
        if filesystem.exists("/etc/app/conf"):
            return 1.0, True, "Service is healthy. Config file restored."
        # Partial credit for diagnostic investigation
        if any("conf" in cmd or "ls" in cmd or "cat" in cmd for cmd in command_history):
            return 0.3, False, "Diagnostic actions detected, but config not yet restored."
        return 0.0, False, "Config file /etc/app/conf is still missing."


class PortGrader(BaseGrader):
    """Grader for t2_port — port 8080 occupied."""

    def grade(
        self,
        filesystem: MockFilesystem,
        process_manager: ProcessManager,
        command_history: list[str],
    ) -> tuple[float, bool, str]:
        if process_manager.is_port_free(8080):
            return 1.0, True, "Service is healthy. Port 8080 is free."
        if any("ps" in cmd or "kill" in cmd for cmd in command_history):
            return 0.3, False, "Diagnostic actions detected, but port 8080 is still occupied."
        return 0.0, False, "Port 8080 is still occupied."


class DependencyGrader(BaseGrader):
    """Grader for t3_dep — missing npm dependency."""

    def grade(
        self,
        filesystem: MockFilesystem,
        process_manager: ProcessManager,
        command_history: list[str],
    ) -> tuple[float, bool, str]:
        has_modules = filesystem.exists("/home/user/app/node_modules/.package-lock.json")
        if has_modules:
            return 1.0, True, "Service is healthy. Dependencies installed and app runs."
        if any("npm" in cmd for cmd in command_history):
            return 0.5, False, "npm command detected but node_modules not found."
        if any("ls" in cmd or "cat" in cmd for cmd in command_history):
            return 0.3, False, "Diagnostic actions detected, but dependencies not installed."
        return 0.0, False, "Missing dependency: dotenv. Run npm install."
