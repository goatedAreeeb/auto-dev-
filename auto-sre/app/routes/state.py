"""GET /state — return rich environment snapshot."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.observation import CommandEntry, RichStateResponse
from app.routes._session import get_session

router = APIRouter()


@router.get("/state", response_model=RichStateResponse)
async def get_state() -> RichStateResponse:
    """Return the current task metadata and full environment snapshot."""
    session = get_session()
    task_def = session.task_def

    # Build visible files list (safe, sandbox only, no recursion)
    files: list[str] = []
    processes: list[str] = []
    cwd = "/home/user"

    if task_def is not None:
        try:
            files = session.sandbox.fs.get_all_paths()[:20]
        except Exception:
            files = []
        try:
            processes = [
                f"{p.pid} {p.command}" + (f" (:{','.join(str(pt) for pt in p.port_bindings)})" if p.port_bindings else "")
                for p in session.sandbox.pm.list_alive()
            ]
        except Exception:
            processes = []
        cwd = session.sandbox.cwd

    # Last command info
    last = session.last_entry
    last_command = last["command"] if last else None
    last_stdout = last["stdout"] if last else ""
    last_stderr = last["stderr"] if last else ""

    # Rolling history
    history = [CommandEntry(**e) for e in session.command_history_full]

    return RichStateResponse(
        # Original StateResponse fields (preserved)
        task_id=task_def.task_id if task_def else None,
        step_count=session.step_count,
        health_status=session.is_done and session.step_count > 0,
        is_done=session.is_done,
        # Extended fields
        current_task=task_def.task_id if task_def else None,
        task_description=task_def.description if task_def else None,
        max_steps=task_def.max_steps if task_def else 0,
        cwd=cwd,
        files=files,
        processes=processes,
        last_command=last_command,
        last_stdout=last_stdout,
        last_stderr=last_stderr,
        history=history,
    )
