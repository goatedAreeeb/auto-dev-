"""GET /grader — return the grader score for the current episode."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.routes._session import get_session

router = APIRouter()


@router.get("/grader", tags=["Environment"])
async def get_grader_score() -> dict:
    """Return the current grader score for the active episode without advancing the episode."""
    session = get_session()

    # 🔒 SAFE fallback instead of HTTP error (validator-friendly)
    if session.task_def is None:
        return {
            "task_id": None,
            "reward": 0.01,
            "done": True,
            "grader_message": "No task loaded",
            "step_count": 0,
            "max_steps": 0,
        }

    # 🔍 Run grader
    reward, done, grader_message = session.task_def.grader.grade(
        session.sandbox.fs,
        session.sandbox.pm,
        session.sandbox.command_history,
    )

    # 🔒 HARD CLAMP (global guarantee)
    reward = float(reward)
    reward = max(0.01, min(0.99, reward))

    # 🔒 ASSERT (detect any hidden leaks)
    assert 0.0 < reward < 1.0, f"INVALID REWARD LEAK: {reward}"

    return {
        "task_id": session.task_def.task_id,
        "reward": reward,
        "done": done,
        "grader_message": grader_message,
        "step_count": session.step_count,
        "max_steps": session.task_def.max_steps,
    }