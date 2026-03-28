from fastapi import FastAPI
from pydantic import BaseModel
from environment import EmailTriageEnv

app = FastAPI()
env = EmailTriageEnv()

class ActionInput(BaseModel):
    classifications: dict[str, str]
    departments: dict[str, str]

@app.get("/")
def root():
    return {"status": "ok", "env": "email-triage"}

@app.post("/reset")
def reset(task_id: str = "easy"):
    obs = env.reset(task_id)
    return obs

@app.post("/step")
def step(action: ActionInput):
    result = env.step(action.model_dump())
    return result

@app.get("/state")
def state():
    return env.state()