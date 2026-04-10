"""
Multi-step inference agent for the Python REPL Debugging Environment.

The agent:
  1. Receives broken code + task description
  2. Iteratively: run code → read error → edit code → run again
  3. Submits when confident the code is correct (or hits step limit)

Logs follow the required OpenEnv format:
  [START] task=<id>
  [STEP] step=<n> action=<type> reward=<r> done=<bool>
  [END] success=<bool> steps=<n> score=<f> rewards=<r1,r2,...>
"""

import subprocess
import sys

subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "requests", "openai"])

import os
import json
import re
import requests
from openai import OpenAI

# ── Config ────────────────────────────────────────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.getenv("MODEL_NAME",   "meta-llama/Llama-3.3-70B-Instruct")
HF_TOKEN     = os.getenv("HF_TOKEN")
ENV_URL      = os.getenv("ENV_URL",      "http://localhost:7860")

client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
TASKS = ["easy", "medium", "hard"]
MAX_AGENT_STEPS = 8   # agent budget per task


# ── Prompt helpers ────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are an expert Python debugger. You will be given broken Python code and a description of what it should do.
You interact with a REPL environment using JSON actions.

Available actions (respond with ONLY a JSON object, no prose):

1. Run the current code to see errors:
   {"action_type": "run_code"}

2. Edit the code (replace entirely with fixed version):
   {"action_type": "edit_code", "code": "<your corrected Python code here>"}

3. Submit your final answer for grading:
   {"action_type": "submit", "code": "<your final corrected Python code here>"}

Strategy:
- First, read the task description and broken code carefully.
- Use run_code to understand the current errors.
- Use edit_code to fix bugs, then run_code again to verify.
- When all tests should pass, use submit.
- You have at most {max_steps} steps total — be efficient.
"""

def build_user_message(obs: dict, history: list[str]) -> str:
    parts = [
        f"TASK: {obs['task_description']}",
        f"\nCURRENT CODE:\n```python\n{obs['current_code']}\n```",
    ]
    if obs.get("stdout"):
        parts.append(f"\nLAST STDOUT:\n{obs['stdout']}")
    if obs.get("stderr"):
        parts.append(f"\nLAST STDERR:\n{obs['stderr']}")
    if history:
        parts.append(f"\nACTIONS SO FAR: {', '.join(history)}")
    parts.append(f"\nStep {obs['step_count']}/{obs['max_steps']}. What is your next action?")
    return "\n".join(parts)


def parse_action(raw: str) -> dict:
    """Extract JSON action from model output."""
    raw = raw.strip()
    # Try direct parse
    try:
        return json.loads(raw)
    except Exception:
        pass
    # Try extracting JSON block
    match = re.search(r'\{.*?\}', raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass
    # Fallback: run the code as-is
    return {"action_type": "run_code"}


# ── Task runner ───────────────────────────────────────────────────────

def run_task(task_id: str) -> float:
    print(f"[START] task={task_id}", flush=True)

    rewards = []
    steps = 0
    success = False

    try:
        # Reset environment
        obs = requests.post(
            f"{ENV_URL}/reset",
            params={"task_id": task_id},
            timeout=30
        ).json()

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT.format(max_steps=MAX_AGENT_STEPS)}
        ]
        action_history = []

        for step_num in range(1, MAX_AGENT_STEPS + 1):
            # Build prompt from current observation
            user_msg = build_user_message(obs, action_history)
            messages.append({"role": "user", "content": user_msg})

            # Call LLM
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=0.0,
                max_tokens=1024,
            )
            raw_reply = response.choices[0].message.content.strip()
            messages.append({"role": "assistant", "content": raw_reply})

            # Parse action
            action = parse_action(raw_reply)
            action_type = action.get("action_type", "run_code")
            action_history.append(action_type)

            # Send action to environment
            result = requests.post(
                f"{ENV_URL}/step",
                json=action,
                timeout=30
            ).json()

            reward = result.get("reward", 0.0)
            done   = result.get("done", False)
            rewards.append(reward)
            steps = step_num

            print(
                f"[STEP] step={step_num} action={action_type} "
                f"reward={reward} done={done}",
                flush=True
            )

            obs = result  # next observation is the step result

            if done:
                # Check if we passed enough tests
                test_results = result.get("test_results", [])
                if test_results:
                    passed = sum(1 for t in test_results if t["passed"])
                    total  = len(test_results)
                    success = (passed == total)
                else:
                    success = reward >= 0.8
                break

    except Exception as e:
        print(f"[ERROR] task={task_id} error={e}", flush=True)

    final_score = rewards[-1] if rewards else 0.0
    rewards_str = ",".join(str(r) for r in rewards)

    print(
        f"[END] success={success} steps={steps} "
        f"score={final_score} rewards={rewards_str}",
        flush=True
    )

    return final_score


# ── Entry point ───────────────────────────────────────────────────────

if __name__ == "__main__":
    total = 0.0
    for task in TASKS:
        total += run_task(task)
    avg = round(total / len(TASKS), 4)
    print(f"[END] average_score={avg}", flush=True)