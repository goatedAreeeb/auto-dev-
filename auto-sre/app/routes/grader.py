"""GET /grader — return the grader score for the current episode."""

from __future__ import annotations

import math
from typing import Optional

from fastapi import APIRouter, Query
from app.routes._session import get_session

router = APIRouter()

_SCORE_MIN = 0.01
_SCORE_MAX = 0.989


def _safe_reward(raw) -> float:
    if raw is None or (isinstance(raw, float) and math.isnan(raw)):
        return _SCORE_MIN
    r = float(raw)
    r = max(_SCORE_MIN, min(_SCORE_MAX, r))
    assert 0 < r < 1, f"Score out of range: {r}"
    return r


@router.get("/grader", tags=["Environment"])
async def get_grader_score(task_id: Optional[str] = Query(default=None)) -> dict:
    """Return the current grader score for the active episode.

    BUG-02 FIX: accepts optional task_id query param.
    If provided, validates it matches the session's loaded task before grading.
    Prevents cross-task reward contamination in training loops.
    """
    session = get_session()

    if session.task_def is None:
        return {
            "task_id": None,
            "reward": _SCORE_MIN,
            "score": _SCORE_MIN,
            "done": True,
            "grader_message": "No task loaded",
            "step_count": 0,
            "max_steps": 0,
        }

    # BUG-02 FIX: validate task_id matches if provided
    if task_id is not None and task_id != session.task_def.task_id:
        return {
            "task_id": task_id,
            "reward": 0.0,
            "score": 0.0,
            "done": False,
            "error": "task_id mismatch",
            "grader_message": (
                f"Requested task_id='{task_id}' but session has '{session.task_def.task_id}' loaded. "
                "Call /reset with the correct task_id first."
            ),
        }

    reward, done, grader_message = session.task_def.grader.grade(
        session.sandbox.fs,
        session.sandbox.pm,
        session.sandbox.command_history,
        session.sandbox.state,
    )
    reward = _safe_reward(reward)

    return {
        "task_id": session.task_def.task_id,
        "reward": reward,
        "score": reward,
        "done": done,
        "grader_message": grader_message,
        "step_count": session.step_count,
        "max_steps": session.task_def.max_steps,
    }


DOCSTRING = """
Evaluate task success based STRICTLY on system state transitions.

The reward is derived purely from system health (e.g., config_fixed, app_running, disk_freed, rogue_dead).
There is ZERO command string matching used for the core reward.
Rewards map to real environment interaction, not text generation.
"""

@router.get("/grade/task_1", tags=["Environment"], summary="Grade Task 1", description=DOCSTRING)
async def grade_task_1() -> dict:
    session = get_session()
    try:
        if not session.task_def or session.task_def.task_id != "t1_config": session.load_task("t1_config")
        reward, _, _ = session.task_def.grader.grade(session.sandbox.fs, session.sandbox.pm, session.sandbox.command_history, session.sandbox.state)
        reward = _safe_reward(reward)
        return {"score": reward, "reward": reward}
    except Exception: return {"score": _SCORE_MIN, "reward": _SCORE_MIN}

@router.get("/grade/task_2", tags=["Environment"], summary="Grade Task 2", description=DOCSTRING)
async def grade_task_2() -> dict:
    session = get_session()
    try:
        if not session.task_def or session.task_def.task_id != "t2_port": session.load_task("t2_port")
        reward, _, _ = session.task_def.grader.grade(session.sandbox.fs, session.sandbox.pm, session.sandbox.command_history, session.sandbox.state)
        reward = _safe_reward(reward)
        return {"score": reward, "reward": reward}
    except Exception: return {"score": _SCORE_MIN, "reward": _SCORE_MIN}

@router.get("/grade/task_3", tags=["Environment"], summary="Grade Task 3", description=DOCSTRING)
async def grade_task_3() -> dict:
    session = get_session()
    try:
        if not session.task_def or session.task_def.task_id != "t3_dep": session.load_task("t3_dep")
        reward, _, _ = session.task_def.grader.grade(session.sandbox.fs, session.sandbox.pm, session.sandbox.command_history, session.sandbox.state)
        reward = _safe_reward(reward)
        return {"score": reward, "reward": reward}
    except Exception: return {"score": _SCORE_MIN, "reward": _SCORE_MIN}

@router.get("/grade/task_4", tags=["Environment"], summary="Grade Task 4", description=DOCSTRING)
async def grade_task_4() -> dict:
    session = get_session()
    try:
        if not session.task_def or session.task_def.task_id != "t4_trap": session.load_task("t4_trap")
        reward, _, _ = session.task_def.grader.grade(session.sandbox.fs, session.sandbox.pm, session.sandbox.command_history, session.sandbox.state)
        reward = _safe_reward(reward)
        return {"score": reward, "reward": reward}
    except Exception: return {"score": _SCORE_MIN, "reward": _SCORE_MIN}

@router.get("/grade/{task_id}", tags=["Environment"], summary="Grade Any Task", description=DOCSTRING)
async def grade_any_task(task_id: str) -> dict:
    session = get_session()
    try:
        if not session.task_def or session.task_def.task_id != task_id: session.load_task(task_id)
        reward, _, _ = session.task_def.grader.grade(session.sandbox.fs, session.sandbox.pm, session.sandbox.command_history, session.sandbox.state)
        reward = _safe_reward(reward)
        return {"score": reward, "reward": reward}
    except Exception: return {"score": _SCORE_MIN, "reward": _SCORE_MIN}
