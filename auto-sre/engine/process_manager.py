"""Mock process manager for simulating running services."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MockProcess:
    """Represents a running process in the mock environment."""

    pid: int
    command: str
    port_bindings: list[int] = field(default_factory=list)
    is_alive: bool = True


class ProcessManager:
    """Manages the mock process table (PIDs, port bindings)."""

    def __init__(self) -> None:
        self._processes: dict[int, MockProcess] = {}
        self._next_pid: int = 1000

    # ── Setup ───────────────────────────────────────────────────────

    def load(self, processes: list[MockProcess]) -> None:
        """Populate the process table (called during reset)."""
        self._processes.clear()
        for proc in processes:
            self._processes[proc.pid] = proc

    def clear(self) -> None:
        """Clear all processes."""
        self._processes.clear()
        self._next_pid = 1000

    # ── Queries ─────────────────────────────────────────────────────

    def list_processes(self) -> list[MockProcess]:
        """Return all processes (alive and dead)."""
        return list(self._processes.values())

    def list_alive(self) -> list[MockProcess]:
        """Return only alive processes."""
        return [p for p in self._processes.values() if p.is_alive]

    def get_by_pid(self, pid: int) -> MockProcess | None:
        """Lookup a process by PID."""
        return self._processes.get(pid)

    def is_port_free(self, port: int) -> bool:
        """Check whether a given port is not bound by any alive process."""
        return not any(port in p.port_bindings for p in self._processes.values() if p.is_alive)

    def find_by_port(self, port: int) -> list[MockProcess]:
        """Find alive processes binding a specific port."""
        return [p for p in self._processes.values() if p.is_alive and port in p.port_bindings]

    # ── Mutations ───────────────────────────────────────────────────

    def kill(self, pid: int) -> bool:
        """Kill a process by PID.  Returns True if found and killed."""
        proc = self._processes.get(pid)
        if proc and proc.is_alive:
            proc.is_alive = False
            return True
        return False

    def spawn(self, command: str, port_bindings: list[int] | None = None) -> MockProcess:
        """Spawn a new mock process."""
        proc = MockProcess(
            pid=self._next_pid,
            command=command,
            port_bindings=port_bindings or [],
            is_alive=True,
        )
        self._processes[proc.pid] = proc
        self._next_pid += 1
        return proc

    # ── Display (for ps aux) ────────────────────────────────────────

    def ps_output(self) -> str:
        """Generate a realistic 'ps aux'-like text output."""
        lines = ["USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND"]
        lines.append(f"root         1  0.0  0.1  10232  4096 ?        Ss   09:00   0:02 /sbin/init")
        for p in self._processes.values():
            if p.is_alive:
                lines.append(f"app       {p.pid:<4}  0.2  1.4 100432 12048 ?        Sl   09:01   0:15 {p.command}")
        return "\n".join(lines)

    def netstat_output(self) -> str:
        """Generate realistic 'netstat -tulpn' or 'lsof -i' style output."""
        lines = ["Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name"]
        for p in self._processes.values():
            if p.is_alive:
                for port in p.port_bindings:
                    lines.append(f"tcp        0      0 0.0.0.0:{port:<15} 0.0.0.0:*               LISTEN      {p.pid}/{p.command.split()[0].split('/')[-1]}")
        return "\n".join(lines)
