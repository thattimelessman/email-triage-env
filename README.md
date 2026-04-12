---
title: Python REPL Debugging Environment
emoji: 🐍
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# 🐍 Python REPL Debugging Environment

> A multi-step RL environment where an agent iteratively debugs broken Python code — running code, reading errors, editing, and submitting for grading.

**Live:** `https://thattimelessman-email-triage-env.hf.space`

---

## Why This Environment Matters

Code debugging is one of the most universal and high-value tasks in software engineering. Training RL agents to debug code has direct real-world applications:

- **Automated bug fixing** in CI/CD pipelines
- **Code review assistance** for developers
- **Educational tutoring systems** that guide students to fix their own bugs
- **LLM fine-tuning** for code repair tasks

Unlike static benchmarks, this environment gives agents a **live REPL loop** — the same feedback cycle human developers use. The agent must reason about error messages, form hypotheses, and iteratively improve its solution.

---

## Environment Design

### Action Space
| Action | Description |
|--------|-------------|
| `run_code` | Execute current code, observe stdout/stderr |
| `edit_code` | Replace current code with a fixed version |
| `submit` | Grade against all test cases, ends episode |

### Observation Space
Each step returns a structured observation:
```json
{
  "episode_id": "uuid",
  "task_id": "easy",
  "task_description": "Fix sum_evens and is_palindrome...",
  "current_code": "def sum_evens(n): ...",
  "stdout": "",
  "stderr": "AssertionError: Expected 30, got 15",
  "step_count": 2,
  "max_steps": 10,
  "done": false,
  "reward": 0.05,
  "message": "Code executed."
}
```

### Reward Shaping
Rewards are **strictly between 0 and 1**:
- `run_code` with errors → `0.05`
- `run_code` clean → `0.10`
- `submit` with partial tests passing → `0.02 + (passed/total) * 0.93`
- `submit` with all tests passing → `0.95`

Partial credit encourages the agent to make incremental progress rather than random submissions.

### Episode Lifecycle
- Each `/reset` call creates an **isolated session** by `episode_id`
- Multiple agents can run **concurrently** without interference
- Episodes end on `submit` or when `max_steps` is reached
- All code runs in a **sandboxed exec context** — no filesystem or network access

---

## Task Curriculum

4 difficulty levels provide a meaningful training curriculum:

| Task | Difficulty | Tests | Bugs | What to Fix |
|------|-----------|-------|------|-------------|
| `easy` | ⭐ | 5 | 3 | Off-by-one in range, wrong modulo operator, broken slice |
| `medium` | ⭐⭐ | 6 | 3 | Wrong division, swapped grade labels, missing sort |
| `hard` | ⭐⭐⭐ | 5 | 5 | Priority queue with wrong tuple order, sort key, pop index, return value, off-by-one |
| `expert` | ⭐⭐⭐⭐ | 6 | 3 | LRU Cache missing order updates in get/put, off-by-one in size |

Each task is designed so bugs **interact** — fixing one reveals the next, forcing the agent to reason across multiple steps.

---

## API Reference

```
GET  /          Health check, lists tasks and actions
GET  /health    Health check
GET  /tasks     List all tasks with descriptions and test counts
POST /reset     Start new episode (?task_id=easy|medium|hard|expert)
POST /step      Take an action
GET  /state     Current episode state (read-only)
```

### Example Session
```bash
# 1. Start episode
curl -X POST "https://thattimelessman-email-triage-env.hf.space/reset?task_id=easy"

# 2. Run broken code to see errors
curl -X POST "https://thattimelessman-email-triage-env.hf.space/step" \
  -H "Content-Type: application/json" \
  -d '{"action_type": "run_code", "episode_id": "<id>"}'

# 3. Submit fixed code
curl -X POST "https://thattimelessman-email-triage-env.hf.space/step" \
  -H "Content-Type: application/json" \
  -d '{"action_type": "submit", "code": "def sum_evens(n):\n    return sum(i for i in range(0, n+1) if i % 2 == 0)", "episode_id": "<id>"}'
```

---

## Python Client

```python
from client import REPLClient

client = REPLClient("https://thattimelessman-email-triage-env.hf.space")

obs = client.reset("hard")
print(obs.task_description)

result = client.step_run_code()
print(result.stderr)

result = client.step_edit_code("class TaskQueue: ...")
result = client.step_submit("class TaskQueue: ...")
print(result.reward, result.success)  # 0.95, True
```

---

## Running the Inference Agent

```bash
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
export HF_TOKEN="your_hf_token"
export ENV_URL="https://thattimelessman-email-triage-env.hf.space"
python inference.py
```

Expected trajectory:
```
[START] task=easy
[STEP] step=1 action=run_code reward=0.05 done=False
[STEP] step=2 action=edit_code reward=0.05 done=False
[STEP] step=3 action=submit reward=0.95 done=True
[INFO] tests=5/5
[END] success=True steps=3 score=0.95 rewards=0.05,0.05,0.95
[END] average_score=0.95
```

---

## Local Development

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 7860
```

## Docker

```bash
docker build -t python-repl-debug-env .
docker run -p 7860:7860 python-repl-debug-env
```

---

## Design Decisions

**Per-session isolation** — Each `/reset` creates a fresh `REPLEnv` instance stored by `episode_id`. Multiple concurrent agents never share state.

**Sandboxed execution** — Agent code runs in an isolated `exec` context with captured stdout/stderr. No filesystem or network access.

**Partial credit grading** — Reward scales linearly with fraction of tests passed, giving the agent a smooth gradient rather than sparse 0/1 signal.

**Interacting bugs** — Tasks are designed so bugs compound. The hard task has 5 bugs across a single class that must all be fixed for full credit.

**4-level curriculum** — easy → medium → hard → expert provides a natural difficulty progression suitable for curriculum learning in RL training.