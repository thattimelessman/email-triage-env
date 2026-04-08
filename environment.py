import random
from typing import Any
from pydantic import BaseModel
from tasks import TASKS


class Observation(BaseModel):
    task_id: str
    emails: list[dict]
    instructions: str


class Action(BaseModel):
    classifications: dict[str, str]   # email_id -> "urgent" / "normal" / "spam"
    departments: dict[str, str]        # email_id -> department name


class Reward(BaseModel):
    score: float
    feedback: str


class EmailTriageEnv:
    def __init__(self):
        self.current_task = None
        self.current_obs = None
        self.done = False

    def reset(self, task_id: str = "easy") -> dict:
        task = TASKS[task_id]
        self.current_task = task
        self.done = False
        self.current_obs = Observation(
            task_id=task_id,
            emails=task["emails"],
            instructions=task["description"]
        )
        return self.current_obs.model_dump()

    def step(self, action: dict) -> dict:
        if self.done:
            return {
                "observation": self.current_obs.model_dump(),
                "reward": 0.0,
                "done": True,
                "info": {"error": "Episode already done. Call reset()."}
            }

        act = Action(**action)
        reward = self._grade(act)
        self.done = True

        return {
            "observation": self.current_obs.model_dump(),
            "reward": reward.score,
            "done": True,
            "info": {"feedback": reward.feedback}
        }

    def state(self) -> dict:
        return {
            "task_id": self.current_task["id"] if self.current_task else None,
            "done": self.done,
            "current_observation": self.current_obs.model_dump() if self.current_obs else None
        }

    def _grade(self, action: Action) -> Reward:
        task = self.current_task
        correct_labels = task["correct_labels"]
        correct_depts = task["correct_departments"]

        total = len(correct_labels)
        label_score = 0
        dept_score = 0

        for email_id, correct_label in correct_labels.items():
            if action.classifications.get(email_id, "").lower() == correct_label:
                label_score += 1

        for email_id, correct_dept in correct_depts.items():
            if action.departments.get(email_id, "").lower() == correct_dept:
                dept_score += 1

        # bonus for phishing detection on hard task
        phishing_bonus = 0.0
        if "phishing_ids" in task:
            phishing_ids = task["phishing_ids"]
            detected = [
                eid for eid in phishing_ids
                if action.classifications.get(eid, "").lower() == "spam"
            ]
            phishing_bonus = 0.1 * (len(detected) / len(phishing_ids))

        raw_score = (label_score / total) * 0.5 + (dept_score / total) * 0.4 + phishing_bonus
        final_score = round(min(raw_score, 0.99), 4) 
        final_score = max(final_score, 0.01)

        feedback = (
            f"Label accuracy: {label_score}/{total} | "
            f"Department accuracy: {dept_score}/{total} | "
            f"Score: {final_score}"
        )

        return Reward(score=final_score, feedback=feedback)