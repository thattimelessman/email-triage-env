"""
Python REPL Debugging Environment — typed client.

Usage:
    from client import REPLClient

    client = REPLClient("https://thattimelessman-email-triage-env.hf.space")
    obs = client.reset("easy")
    print(obs.task_description)

    result = client.step_run_code()
    result = client.step_edit_code("def sum_evens(n): ...")
    result = client.step_submit("def sum_evens(n): ...")
    print(result.reward, result.success)
"""

from __future__ import annotations
import requests
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TestResult:
    test_name: str
    passed: bool
    stderr: str = ""


@dataclass
class Observation:
    episode_id: str
    task_id: str
    task_description: str
    current_code: str
    stdout: str
    stderr: str
    step_count: int
    max_steps: int
    done: bool
    reward: float
    message: str
    test_results: list[TestResult] = field(default_factory=list)

    @property
    def success(self) -> bool:
        if self.test_results:
            return all(t.passed for t in self.test_results)
        return self.reward >= 0.9

    @classmethod
    def from_dict(cls, data: dict) -> "Observation":
        test_results = [
            TestResult(
                test_name=t["test_name"],
                passed=t["passed"],
                stderr=t.get("stderr", ""),
            )
            for t in data.get("test_results", [])
        ]
        return cls(
            episode_id=data.get("episode_id", ""),
            task_id=data.get("task_id", ""),
            task_description=data.get("task_description", ""),
            current_code=data.get("current_code", ""),
            stdout=data.get("stdout", ""),
            stderr=data.get("stderr", ""),
            step_count=data.get("step_count", 0),
            max_steps=data.get("max_steps", 10),
            done=data.get("done", False),
            reward=data.get("reward", 0.0),
            message=data.get("message", ""),
            test_results=test_results,
        )


class REPLClient:
    """
    Synchronous client for the Python REPL Debugging Environment.

    Compatible with the OpenEnv reset/step/state API pattern.
    """

    TASKS = ["easy", "medium", "hard", "expert"]

    def __init__(self, base_url: str = "https://thattimelessman-email-triage-env.hf.space", timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._episode_id: Optional[str] = None

    def health(self) -> dict:
        """Check if the environment server is running."""
        r = requests.get(f"{self.base_url}/health", timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def list_tasks(self) -> list[dict]:
        """List all available tasks with descriptions and test counts."""
        r = requests.get(f"{self.base_url}/tasks", timeout=self.timeout)
        r.raise_for_status()
        return r.json()["tasks"]

    def reset(self, task_id: str = "easy") -> Observation:
        """Start a new debugging episode. Returns initial observation with broken code."""
        if task_id not in self.TASKS:
            raise ValueError(f"Unknown task_id '{task_id}'. Choose from: {self.TASKS}")
        r = requests.post(
            f"{self.base_url}/reset",
            params={"task_id": task_id},
            timeout=self.timeout,
        )
        r.raise_for_status()
        obs = Observation.from_dict(r.json())
        self._episode_id = obs.episode_id
        return obs

    def step(self, action: dict) -> Observation:
        """Send any action dict to the environment."""
        if self._episode_id:
            action = {**action, "episode_id": self._episode_id}
        r = requests.post(
            f"{self.base_url}/step",
            json=action,
            timeout=self.timeout,
        )
        r.raise_for_status()
        return Observation.from_dict(r.json())

    def step_run_code(self, code: Optional[str] = None) -> Observation:
        """Execute current (or provided) code and observe stdout/stderr."""
        action = {"action_type": "run_code"}
        if code:
            action["code"] = code
        return self.step(action)

    def step_edit_code(self, code: str) -> Observation:
        """Replace current code with a new version."""
        return self.step({"action_type": "edit_code", "code": code})

    def step_submit(self, code: Optional[str] = None) -> Observation:
        """Submit current (or provided) code for grading. Ends the episode."""
        action = {"action_type": "submit"}
        if code:
            action["code"] = code
        return self.step(action)

    def state(self) -> dict:
        """Get current episode state without consuming a step."""
        r = requests.get(f"{self.base_url}/state", timeout=self.timeout)
        r.raise_for_status()
        return r.json()


if __name__ == "__main__":
    # Quick smoke test
    client = REPLClient()
    print("Health:", client.health())
    print("Tasks:", [t["id"] for t in client.list_tasks()])

    for task_id in ["easy", "medium", "hard", "expert"]:
        obs = client.reset(task_id)
        print(f"\n[{task_id}] {obs.task_description[:60]}...")
        print(f"  Broken code preview: {obs.current_code[:80].strip()}...")

        result = client.step_run_code()
        print(f"  After run_code: stderr={bool(result.stderr)}, reward={result.reward}")