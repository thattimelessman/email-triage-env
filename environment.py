"""
Python REPL / Code Debugging Environment
Agent receives broken Python code and must fix it by iteratively
running code, reading errors, and applying edits until tests pass.
"""

import uuid
import traceback
import io
import sys
import ast
from contextlib import redirect_stdout, redirect_stderr
from typing import Optional


class REPLEnv:
    """
    Multi-step RL environment where the agent debugs broken Python code.

    Actions:
        - run_code:  execute current code, see stdout/stderr
        - edit_code: replace current code with new version
        - submit:    final submission — triggers grading

    Observation contains:
        - current_code: what's currently in the editor
        - stdout / stderr: output from last run
        - task_description: what the code should do
        - test_results: per-test pass/fail after submit
        - step_count, done, reward
    """

    MAX_STEPS = 10

    def __init__(self):
        self._episode_id: Optional[str] = None
        self._task_id: Optional[str] = None
        self._current_code: str = ""
        self._task: Optional[dict] = None
        self._step_count: int = 0
        self._done: bool = False
        self._last_stdout: str = ""
        self._last_stderr: str = ""
        self._last_reward: float = 0.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def reset(self, task_id: str = "easy") -> dict:
        from tasks import TASKS
        if task_id not in TASKS:
            task_id = "easy"

        self._episode_id = str(uuid.uuid4())
        self._task_id = task_id
        self._task = TASKS[task_id]
        self._current_code = self._task["broken_code"]
        self._step_count = 0
        self._done = False
        self._last_stdout = ""
        self._last_stderr = ""
        self._last_reward = 0.0

        return self._observation(reward=0.0, message="Episode started. Debug the code.")

    def step(self, action: dict) -> dict:
        if self._done:
            return self._observation(reward=0.0, message="Episode already done. Call /reset.")

        action_type = action.get("action_type", "")
        self._step_count += 1

        if action_type == "run_code":
            return self._handle_run(action)
        elif action_type == "edit_code":
            return self._handle_edit(action)
        elif action_type == "submit":
            return self._handle_submit(action)
        else:
            self._last_stderr = f"Unknown action_type '{action_type}'. Use: run_code, edit_code, submit."
            return self._observation(reward=0.0, message="Invalid action.")

    def state(self) -> dict:
        return {
            "episode_id": self._episode_id,
            "task_id": self._task_id,
            "step_count": self._step_count,
            "done": self._done,
            "current_code": self._current_code,
        }

    # ------------------------------------------------------------------
    # Action handlers
    # ------------------------------------------------------------------

    def _handle_run(self, action: dict) -> dict:
        """Run current code (or provided code) in a sandbox."""
        code_to_run = action.get("code", self._current_code)
        stdout, stderr = self._safe_exec(code_to_run)
        self._last_stdout = stdout
        self._last_stderr = stderr

        reward = 0.0
        if not stderr:
            reward = 0.1  # small reward for clean run

        # Step limit check
        if self._step_count >= self.MAX_STEPS:
            self._done = True
            return self._observation(reward=reward, message="Step limit reached.")

        return self._observation(reward=reward, message="Code executed.")

    def _handle_edit(self, action: dict) -> dict:
        """Replace the current code with agent's new version."""
        new_code = action.get("code", "")
        if not new_code.strip():
            return self._observation(reward=0.0, message="Edit rejected: empty code.")

        self._current_code = new_code
        self._last_stdout = ""
        self._last_stderr = ""

        if self._step_count >= self.MAX_STEPS:
            self._done = True
            return self._observation(reward=0.0, message="Step limit reached.")

        return self._observation(reward=0.0, message="Code updated. Use run_code to test it.")

    def _handle_submit(self, action: dict) -> dict:
        """Grade the current code against all test cases."""
        code = action.get("code", self._current_code)
        if action.get("code"):
            self._current_code = code

        results, reward = self._grade(self._current_code)
        self._last_reward = reward
        self._done = True

        passed = sum(1 for r in results if r["passed"])
        total = len(results)
        message = f"Submitted. {passed}/{total} tests passed. Score: {reward:.3f}"

        return self._observation(reward=reward, message=message, test_results=results)

    # ------------------------------------------------------------------
    # Execution sandbox
    # ------------------------------------------------------------------

    def _safe_exec(self, code: str, extra_globals: dict = None) -> tuple[str, str]:
        """Execute code safely, capture stdout/stderr. Returns (stdout, stderr)."""
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        globs = {"__builtins__": __builtins__}
        if extra_globals:
            globs.update(extra_globals)

        try:
            with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
                exec(compile(code, "<agent_code>", "exec"), globs)
        except SyntaxError as e:
            stderr_buf.write(f"SyntaxError: {e}\n")
        except Exception:
            stderr_buf.write(traceback.format_exc())

        return stdout_buf.getvalue(), stderr_buf.getvalue()

    def _grade(self, code: str) -> tuple[list, float]:
        """Run all test cases and compute reward with partial credit."""
        tests = self._task["tests"]
        results = []

        for test in tests:
            test_code = code + "\n\n" + test["assert_code"]
            stdout, stderr = self._safe_exec(test_code)
            passed = not stderr and not stdout.startswith("FAIL")
            results.append({
                "test_name": test["name"],
                "passed": passed,
                "stderr": stderr[:300] if stderr else "",
            })

        n = len(results)
        passed_count = sum(1 for r in results if r["passed"])

        # Weighted partial credit
        base = passed_count / n if n else 0.0
        # Bonus for full pass
        bonus = 0.1 if passed_count == n else 0.0
        # Step efficiency bonus (fewer steps = slightly higher reward)
        efficiency = max(0.0, (self.MAX_STEPS - self._step_count) / self.MAX_STEPS) * 0.1
        reward = round(min(1.0, base + bonus + efficiency), 4)

        return results, reward

    # ------------------------------------------------------------------
    # Response builder
    # ------------------------------------------------------------------

    def _observation(self, reward: float, message: str, test_results: list = None) -> dict:
        obs = {
            "episode_id": self._episode_id,
            "task_id": self._task_id,
            "task_description": self._task["description"] if self._task else "",
            "current_code": self._current_code,
            "stdout": self._last_stdout,
            "stderr": self._last_stderr,
            "step_count": self._step_count,
            "max_steps": self.MAX_STEPS,
            "done": self._done,
            "reward": reward,
            "message": message,
        }
        if test_results is not None:
            obs["test_results"] = test_results
        return obs