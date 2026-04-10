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

# Per-session storage keyed by episode_id
_sessions: dict = {}
_default_env = REPLEnv()  # fallback for stateless clients


class ActionInput(BaseModel):
    action_type: str = Field(..., description="One of: 'run_code', 'edit_code', 'submit'")
    code: Optional[str] = Field(None, description="Code for edit_code or submit actions.")
    episode_id: Optional[str] = Field(None, description="Session ID from /reset response.")


@app.get("/")
def root():
    return {
        "status": "ok",
        "env": "python-repl-debug",
        "description": "Debug broken Python code through iterative REPL interaction.",
        "actions": ["run_code", "edit_code", "submit"],
        "tasks": ["easy", "medium", "hard", "expert"],
    }


@app.get("/health")
def health():
    return {"status": "healthy", "service": "python-repl-debug-env"}


@app.get("/tasks")
def list_tasks():
    from tasks import TASKS
    return {
        "tasks": [
            {"id": tid, "description": t["description"], "num_tests": len(t["tests"])}
            for tid, t in TASKS.items()
        ]
    }


@app.post("/reset")
def reset(task_id: str = Query("easy", description="Task difficulty: easy | medium | hard | expert")):
    env = REPLEnv()
    obs = env.reset(task_id)
    _sessions[obs["episode_id"]] = env
    return obs


@app.post("/step")
def step(action: ActionInput):
    data = action.model_dump()
    episode_id = data.pop("episode_id", None)
    env = _sessions.get(episode_id, _default_env)
    if env._task is None:
        env.reset("easy")
    return env.step(data)


@app.get("/state")
def state():
    return _default_env.state()