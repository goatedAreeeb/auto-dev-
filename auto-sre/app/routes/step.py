"""POST /step — execute one agent action in the sandbox."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.action import DevOpsAction
from app.schemas.observation import Observation, StepResponse
from app.routes._session import get_session
from app.logger import get_logger
from engine.security import CommandNotAllowedError, StepTimeoutError

router = APIRouter()
logger = get_logger("auto-sre.step")


@router.post("/step", response_model=StepResponse)
async def step_action(action: DevOpsAction) -> StepResponse:
    """Execute a shell command and return the resulting observation and reward."""
    session = get_session()

    if session.task_def is None:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "NO_TASK_LOADED",
                "message": "No task loaded. Call POST /reset first.",
            },
        )

    if session.is_done:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "EPISODE_DONE",
                "message": "Episode is already done. Call POST /reset.",
            },
        )

    if session.step_count >= session.task_def.max_steps:
        session.is_done = True
        raise HTTPException(
            status_code=400,
            detail={
                "error": "MAX_STEPS_EXCEEDED",
                "message": "Max steps exceeded. Episode is done.",
            },
        )

    try:
        result = session.sandbox.execute(action.arguments)
        
        # MANDATORY USER ASSERTION: Guarantee stdout is NEVER empty for a successful valid command
        if result.success and not result.stdout and not result.stderr:
            raise Exception("CRITICAL: stdout empty for valid command")
            
    except CommandNotAllowedError as e:
        logger.warning("COMMAND_NOT_ALLOWED command=%r error=%s", action.arguments, e)
        raise HTTPException(
            status_code=400,
            detail={
                "error": "COMMAND_NOT_ALLOWED",
                "message": str(e),
            },
        )
    except StepTimeoutError as e:
        logger.warning("TIMEOUT command=%r", action.arguments)
        raise HTTPException(
            status_code=408,
            detail={
                "error": "TIMEOUT",
                "message": str(e),
            },
        )

    session.step_count += 1

    # Record into rolling history
    session.record_step(action.arguments, result.stdout, result.stderr)

    # Grade
    reward, done, grader_message = session.task_def.grader.grade(
        session.sandbox.fs,
        session.sandbox.pm,
        session.sandbox.command_history,
    )
    session.is_done = done or (session.step_count >= session.task_def.max_steps)

    logger.info(
        "step command=%r reward=%.2f done=%s success=%s",
        action.arguments,
        reward,
        session.is_done,
        result.success,
    )

    observation = Observation(
        stdout=result.stdout,
        stderr=result.stderr,
        cwd=session.sandbox.cwd,
        health_status=done,
    )

    return StepResponse(
        observation=observation,
        reward=reward,
        done=session.is_done,
        info={
            "steps_taken": session.step_count,
            "max_steps": session.task_def.max_steps,
            "grader_message": grader_message,
            "history": list(session.command_history_full),
        },
    )
