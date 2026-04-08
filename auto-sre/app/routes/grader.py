"""GET /grader — return the grader score for the current episode."""

from __future__ import annotations

import math

from fastapi import APIRouter, HTTPException
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
async def get_grader_score() -> dict:
    """Return the current grader score for the active episode without advancing the episode."""
    session = get_session()

    # Safe fallback instead of HTTP error (validator-friendly)
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

    # Run grader
    reward, done, grader_message = session.task_def.grader.grade(
        session.sandbox.fs,
        session.sandbox.pm,
        session.sandbox.command_history,
    )

    # HARD CLAMP (global guarantee)
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


@router.get("/grade/{task_id}", tags=["Environment"])
async def grade_task_by_id(task_id: str) -> dict:
    """Validator-specific endpoint to get the strict grade for a task."""
    session = get_session()

    # Handle validator placeholder testing aliases
    task_map = {
        "task_1": "t1_config",
        "task_2": "t2_port",
        "task_3": "t3_dep",
        "task_4": "t4_trap"
    }
    actual_task_id = task_map.get(task_id, task_id)

    # If the session is active and matches the task, grade the CURRENT simulated state
    if session.task_def and session.task_def.task_id == actual_task_id:
        reward, _, _ = session.task_def.grader.grade(
            session.sandbox.fs,
            session.sandbox.pm,
            session.sandbox.command_history,
        )
        reward = _safe_reward(reward)
        return {"score": reward, "reward": reward}

    # If the validator pings it without a matching active session, try loading it
    try:
        session.load_task(actual_task_id)
        reward, _, _ = session.task_def.grader.grade(
            session.sandbox.fs,
            session.sandbox.pm,
            session.sandbox.command_history,
        )
        reward = _safe_reward(reward)
        return {"score": reward, "reward": reward}
    except Exception:
        return {"score": _SCORE_MIN, "reward": _SCORE_MIN}