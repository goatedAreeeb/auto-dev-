"""Sandbox engine — parses and executes mock shell commands."""

from __future__ import annotations

import shlex
from dataclasses import dataclass, field
from typing import Any

from engine.filesystem import MockFilesystem
from engine.process_manager import ProcessManager
from engine.security import (
    CommandNotAllowedError,
    StepTimeoutError,
    validate_command,
    with_timeout,
    STEP_TIMEOUT_SECONDS,
)


@dataclass
class CommandResult:
    """Result of executing a command in the sandbox."""

    stdout: str = ""
    stderr: str = ""
    success: bool = True


class Sandbox:
    """
    Mock shell that intercepts agent commands and applies them
    against the in-memory filesystem and process manager.
    """

    def __init__(
        self,
        filesystem: MockFilesystem,
        process_manager: ProcessManager,
    ) -> None:
        self.fs = filesystem
        self.pm = process_manager
        self.cwd: str = "/home/user"
        self.command_history: list[str] = []

    # ── Public API ──────────────────────────────────────────────────

    @with_timeout(STEP_TIMEOUT_SECONDS)
    def execute(self, raw_command: str) -> CommandResult:
        """Validate and execute a shell command, returning stdout/stderr."""
        validated = validate_command(raw_command)
        self.command_history.append(validated)

        import os
        parts = shlex.split(validated)
        base = os.path.basename(parts[0])
        args = list(parts[1:])

        handler = self._HANDLERS.get(base)
        if handler is None:
            return CommandResult(stderr=f"Command '{base}' is recognized but has no handler yet.")
        return handler(self, args)

    def reset(self) -> None:
        """Clear command history and reset cwd."""
        self.command_history.clear()
        self.cwd = "/home/user"

    # ── Command handlers ────────────────────────────────────────────

    def _cmd_ls(self, args: list[str]) -> CommandResult:
        import os

        # Separate flags from paths
        paths = [a for a in args if not a.startswith("-")]
        target = paths[0] if paths else self.cwd
        target = self._resolve(target)

        try:
            # 🔥 FIX: use ALL paths instead of list_dir
            all_paths = self.fs.get_all_paths()

            # filter files under directory
            children = [
                os.path.basename(p)
                for p in all_paths
                if p.startswith(target.rstrip("/") + "/")
            ]

            if not children:
                return CommandResult(stdout="total 0")

            return CommandResult(stdout="\n".join(children))

        except Exception as e:
            return CommandResult(stderr=str(e), success=False)

    def _cmd_cat(self, args: list[str]) -> CommandResult:
        # Ignore bash flags like `cat -n` or just take the very last argument as the path
        paths = [a for a in args if not a.startswith("-")]
        if not paths:
            return CommandResult(stderr="cat: missing operand", success=False)
        path = self._resolve(paths[-1])
        try:
            content = self.fs.read(path)
            return CommandResult(stdout=content)
        except FileNotFoundError as e:
            return CommandResult(stderr=str(e), success=False)

    def _cmd_grep(self, args: list[str]) -> CommandResult:
        if len(args) < 2:
            return CommandResult(stderr="grep: missing arguments", success=False)
        pattern, path = args[0], self._resolve(args[1])
        try:
            content = self.fs.read(path)
            matches = [line for line in content.splitlines() if pattern in line]
            return CommandResult(stdout="\n".join(matches))
        except FileNotFoundError as e:
            return CommandResult(stderr=str(e), success=False)

    def _cmd_pwd(self, args: list[str]) -> CommandResult:
        return CommandResult(stdout=self.cwd)

    def _cmd_cd(self, args: list[str]) -> CommandResult:
        target = args[0] if args else "/home/user"
        self.cwd = self._resolve(target)
        return CommandResult(stdout=f"cd: changed to {self.cwd}")

    def _cmd_mv(self, args: list[str]) -> CommandResult:
        if len(args) < 2:
            return CommandResult(stderr="mv: missing operand", success=False)
        src, dst = self._resolve(args[0]), self._resolve(args[1])
        try:
            self.fs.rename(src, dst)
            return CommandResult(stdout=f"mv: moved '{src}' to '{dst}'")
        except FileNotFoundError as e:
            return CommandResult(stderr=str(e), success=False)

    def _cmd_rm(self, args: list[str]) -> CommandResult:
        # Strip flags like -rf
        paths = [a for a in args if not a.startswith("-")]
        if not paths:
            return CommandResult(stderr="rm: missing operand", success=False)
        for p in paths:
            try:
                self.fs.delete(self._resolve(p))
            except FileNotFoundError as e:
                return CommandResult(stderr=str(e), success=False)
        return CommandResult(stdout="rm: deleted targets")

    def _cmd_touch(self, args: list[str]) -> CommandResult:
        if not args:
            return CommandResult(stderr="touch: missing operand", success=False)
        path = self._resolve(args[0])
        if not self.fs.exists(path):
            self.fs.write(path, "")
        return CommandResult(stdout=f"touch: created/updated {path}")

    def _cmd_mkdir(self, args: list[str]) -> CommandResult:
        # Simplified: just acknowledge (directories are implicit)
        return CommandResult(stdout="mkdir: directory created")

    def _cmd_echo(self, args: list[str]) -> CommandResult:
        return CommandResult(stdout=" ".join(args))

    def _cmd_ps(self, args: list[str]) -> CommandResult:
        return CommandResult(stdout=self.pm.ps_output())

    def _cmd_kill(self, args: list[str]) -> CommandResult:
        # Parse: kill -9 <pid>  or  kill <pid>
        pids: list[int] = []
        for a in args:
            if a.startswith("-"):
                continue  # skip signal flags
            try:
                pids.append(int(a))
            except ValueError:
                return CommandResult(stderr=f"kill: invalid PID '{a}'", success=False)
        if not pids:
            return CommandResult(stderr="kill: missing PID", success=False)
        for pid in pids:
            if not self.pm.kill(pid):
                return CommandResult(stderr=f"kill: process {pid} not found", success=False)
        return CommandResult(stdout="kill: signal sent")

    def _cmd_systemctl(self, args: list[str]) -> CommandResult:
        if not args:
            return CommandResult(stderr="systemctl: missing argument", success=False)
        action = args[0]
        service = args[1] if len(args) > 1 else "unknown"
        if action == "status":
            return CommandResult(stdout=f"● {service} - active (running)")
        if action in ("start", "restart"):
            return CommandResult(stdout=f"{service} started.")
        if action == "stop":
            return CommandResult(stdout=f"{service} stopped.")
        return CommandResult(stdout=f"systemctl {action} {service}: done")

    def _cmd_npm(self, args: list[str]) -> CommandResult:
        if args and args[0] == "install":
            # Simulate installing — create node_modules marker
            self.fs.write(self._resolve("node_modules/.package-lock.json"), "{}")
            return CommandResult(stdout="added 42 packages in 3s")
        return CommandResult(stdout="npm: ok")

    def _cmd_pip(self, args: list[str]) -> CommandResult:
        if len(args) > 1 and args[0] == "install":
            args.pop(0)
            return CommandResult(stdout="Successfully installed " + " ".join(args))
        return CommandResult(stdout="pip: ok")

    def _cmd_find(self, args: list[str]) -> CommandResult:
        root = self._resolve(args[0]) if args else self.cwd
        all_paths = self.fs.get_all_paths()
        matches = [p for p in all_paths if p.startswith(root)]
        return CommandResult(stdout="\n".join(matches))

    def _cmd_head(self, args: list[str]) -> CommandResult:
        if not args:
            return CommandResult(stderr="head: missing operand", success=False)
        path = self._resolve(args[-1])
        try:
            content = self.fs.read(path)
            lines = content.splitlines()[:10]
            return CommandResult(stdout="\n".join(lines))
        except FileNotFoundError as e:
            return CommandResult(stderr=str(e), success=False)

    def _cmd_tail(self, args: list[str]) -> CommandResult:
        paths = [a for a in args if not a.startswith("-")]
        if not paths:
            return CommandResult(stderr="tail: missing operand", success=False)
        path = self._resolve(paths[-1])
        try:
            content = self.fs.read(path)
            lines = content.splitlines()[-10:]
            return CommandResult(stdout="\n".join(lines))
        except FileNotFoundError as e:
            return CommandResult(stderr=str(e), success=False)

    def _cmd_netstat(self, args: list[str]) -> CommandResult:
        return CommandResult(stdout=self.pm.netstat_output())

    def _cmd_lsof(self, args: list[str]) -> CommandResult:
        return CommandResult(stdout=self.pm.netstat_output())

    def _cmd_node(self, args: list[str]) -> CommandResult:
        if not args:
            return CommandResult(stdout="", stderr="Usage: node [options] [ script.js ] [arguments]", success=False)
        if args[0] == "app.js":
            # Simulate a real missing dotenv stacktrace if node_modules is missing
            has_deps = self.fs.exists("/home/user/app/node_modules/.package-lock.json")
            if not has_deps:
                trace = (
                    "internal/modules/cjs/loader.js:902\n"
                    "  throw err;\n"
                    "  ^\n\n"
                    "Error: Cannot find module 'dotenv'\n"
                    "Require stack:\n"
                    "- /home/user/app/app.js\n"
                    "    at Function.Module._resolveFilename (internal/modules/cjs/loader.js:902:15)\n"
                    "    at Function.Module._load (internal/modules/cjs/loader.js:746:27)\n"
                    "    at Module.require (internal/modules/cjs/loader.js:974:19)\n"
                    "    at require (internal/modules/cjs/helpers.js:101:18)\n"
                    "    at Object.<anonymous> (/home/user/app/app.js:1:1)"
                )
                return CommandResult(stderr=trace, success=False)
            return CommandResult(stdout="Server listening on port 3000")
        return CommandResult(stdout="node: interpreted successfully")

    # ── Helpers ─────────────────────────────────────────────────────

    def _resolve(self, path: str) -> str:
        """Resolve a path relative to cwd (very simplified)."""
        if path.startswith("/"):
            return path
        return self.cwd.rstrip("/") + "/" + path

    # Map base command names → handler methods
    _HANDLERS: dict[str, Any] = {}


# Register handlers after class is defined
Sandbox._HANDLERS = {
    "ls": Sandbox._cmd_ls,
    "cat": Sandbox._cmd_cat,
    "grep": Sandbox._cmd_grep,
    "pwd": Sandbox._cmd_pwd,
    "cd": Sandbox._cmd_cd,
    "mv": Sandbox._cmd_mv,
    "rm": Sandbox._cmd_rm,
    "touch": Sandbox._cmd_touch,
    "mkdir": Sandbox._cmd_mkdir,
    "echo": Sandbox._cmd_echo,
    "ps": Sandbox._cmd_ps,
    "kill": Sandbox._cmd_kill,
    "systemctl": Sandbox._cmd_systemctl,
    "npm": Sandbox._cmd_npm,
    "pip": Sandbox._cmd_pip,
    "find": Sandbox._cmd_find,
    "head": Sandbox._cmd_head,
    "tail": Sandbox._cmd_tail,
    "netstat": Sandbox._cmd_netstat,
    "lsof": Sandbox._cmd_lsof,
    "node": Sandbox._cmd_node,
}
