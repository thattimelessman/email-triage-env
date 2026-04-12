---
title: Python REPL Debugging Environment
emoji: 🐍
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# Python REPL Debugging Environment

A multi-step RL environment where an agent debugs broken Python code by iteratively running code, reading errors, and applying fixes until all test cases pass.

## Overview

This environment presents an agent with broken Python code and a task description. The agent must identify and fix all bugs through a REPL-style interaction loop — running code, observing errors, editing, and finally submitting for grading.

Built on FastAPI, deployed on Hugging Face Spaces, and fully compatible with the OpenEnv spec.

## Environment Details

**Actions**
- `run_code` — Execute current code, observe stdout/stderr
- `edit_code` — Replace current code with a fixed version
- `submit` — Grade current code against all test cases (ends episode)

**Observation**
Each step returns: current code, stdout, stderr, step count, task description, reward, and done flag.

**Reward**
Scores are strictly between 0 and 1, remapped from fraction of tests passed:
- 0 tests passing → 0.02
- All tests passing → 0.95
- Partial credit for each passing test

**Episodes**
Each episode is isolated via a unique `episode_id`. Multiple agents can run concurrently without interference.

## Tasks

| Task | Difficulty | Tests | Description |
|------|-----------|-------|-------------|
| `easy` | Easy | 5 | Fix `sum_evens` and `is_palindrome` functions |
| `medium` | Medium | 6 | Fix a student grade processor pipeline |
| `hard` | Hard | 5 | Fix a priority task scheduler with 5 bugs |
| `expert` | Expert | 6 | Fix an LRU Cache with 4 interacting bugs |

## API Endpoints

```
GET  /          — Health check, lists tasks and actions
GET  /health    — Health check
GET  /tasks     — List all tasks with descriptions
POST /reset     — Start new episode (?task_id=easy|medium|hard|expert)
POST /step      — Take an action (run_code, edit_code, submit)
GET  /state     — Current episode state
```

## Quick Start

```bash
# Reset environment
curl -X POST "https://thattimelessman-email-triage-env.hf.space/reset?task_id=easy"

# Run current code
curl -X POST "https://thattimelessman-email-triage-env.hf.space/step" \
  -H "Content-Type: application/json" \
  -d '{"action_type": "run_code", "episode_id": "<id from reset>"}'

# Submit fixed code
curl -X POST "https://thattimelessman-email-triage-env.hf.space/step" \
  -H "Content-Type: application/json" \
  -d '{"action_type": "submit", "code": "def sum_evens(n):\n    ...", "episode_id": "<id>"}'
```

## Running the Agent

```bash
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
export HF_TOKEN="your_hf_token"
export ENV_URL="https://thattimelessman-email-triage-env.hf.space"
python inference.py
```

Expected output:
```
[START] task=easy
[STEP] step=1 action=run_code reward=0.05 done=False
[STEP] step=2 action=edit_code reward=0.05 done=False
[STEP] step=3 action=submit reward=0.95 done=True
[INFO] tests=5/5
[END] success=True steps=3 score=0.95 rewards=0.05,0.05,0.95
[END] average_score=0.95
```

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

## Design Decisions

- **Per-session isolation**: Each `/reset` call creates a new `REPLEnv` instance stored by `episode_id`, allowing concurrent agents without state conflicts.
- **Sandboxed execution**: Agent code runs in an isolated `exec` context with captured stdout/stderr — no filesystem or network access.
- **Partial credit grading**: Reward scales with fraction of tests passed, encouraging the agent to make incremental progress rather than random submissions.
- **4 difficulty levels**: Progression from trivial single-function bugs to multi-class interacting bugs, providing a meaningful training curriculum.