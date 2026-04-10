"""
Python REPL Debugging Environment — OpenEnv-compatible FastAPI server.

Endpoints:
  GET  /          health check
  GET  /health    health check
  POST /reset     start a new episode (param: task_id = easy|medium|hard)
  POST /step      take an action
  GET  /state     current episode state
"""

from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from typing import Optional
from environment import REPLEnv

app = FastAPI(
    title="Python REPL Debugging Environment",
    description=(
        "An OpenEnv-compatible RL environment where an agent debugs broken Python code. "
        "The agent iteratively runs code, reads errors, edits, and submits for grading."
    ),
    version="1.0.0",
)

env = REPLEnv()


# ── Action model ──────────────────────────────────────────────────────

class ActionInput(BaseModel):
    action_type: str = Field(
        ...,
        description="One of: 'run_code', 'edit_code', 'submit'",
        examples=["run_code", "edit_code", "submit"],
    )
    code: Optional[str] = Field(
        None,
        description=(
            "For 'run_code': code to execute (omit to run current code). "
            "For 'edit_code': the new code to save. "
            "For 'submit': final code to grade (omit to grade current code)."
        ),
    )


# ── Routes ───────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "status": "ok",
        "env": "python-repl-debug",
        "description": "Debug broken Python code through iterative REPL interaction.",
        "actions": ["run_code", "edit_code", "submit"],
        "tasks": ["easy", "medium", "hard"],
    }


@app.get("/health")
def health():
    return {"status": "healthy", "service": "python-repl-debug-env"}


@app.post("/reset")
def reset(task_id: str = Query("easy", description="Task difficulty: easy | medium | hard")):
    """
    Start a new debugging episode. Returns the initial observation including
    the broken code and task description.
    """
    return env.reset(task_id)


@app.post("/step")
def step(action: ActionInput):
    """
    Take one action in the environment.

    - **run_code**: execute current (or provided) code, receive stdout/stderr
    - **edit_code**: replace current code with new version
    - **submit**: grade current code against test suite, ends episode
    """
    return env.step(action.model_dump())


@app.get("/state")
def state():
    """Return current episode state (read-only, does not consume a step)."""
    return env.state()