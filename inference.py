import subprocess, sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "requests"])
import os, json, re, requests

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.getenv("MODEL_NAME",   "meta-llama/Llama-3.3-70B-Instruct")
HF_TOKEN     = os.getenv("HF_TOKEN")
ENV_URL      = os.getenv("ENV_URL",      "http://localhost:7860")
TASKS        = ["easy", "medium", "hard"]
MAX_STEPS    = 8

SYSTEM = (
    "You are an expert Python debugger. "
    "Respond with ONLY a raw JSON object, no markdown, no explanation.\n\n"
    "Actions:\n"
    '  {"action_type": "run_code"}\n'
    '  {"action_type": "edit_code", "code": "<full fixed code>"}\n'
    '  {"action_type": "submit",    "code": "<full fixed code>"}\n\n'
    "Strategy: run_code to see errors, edit_code to fix, submit when done."
)

def call_llm(messages):
    r = requests.post(
        API_BASE_URL + "/chat/completions",
        headers={"Authorization": "Bearer " + HF_TOKEN, "Content-Type": "application/json"},
        json={"model": MODEL_NAME, "messages": messages, "temperature": 0.0, "max_tokens": 1024},
        timeout=60,
    )
    r.raise_for_status()
    return (r.json()["choices"][0]["message"].get("content") or "").strip()

def build_msg(obs, history):
    parts = ["TASK: " + obs["task_description"], "CODE:\n" + obs["current_code"]]
    if obs.get("stdout"): parts.append("STDOUT:\n" + obs["stdout"])
    if obs.get("stderr"): parts.append("STDERR:\n" + obs["stderr"])
    if history: parts.append("ACTIONS SO FAR: " + ", ".join(history))
    parts.append("Step " + str(obs["step_count"]) + "/" + str(obs["max_steps"]) + ". JSON only.")
    return "\n".join(parts)

def parse_action(raw):
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"\s*```\s*$",      "", raw, flags=re.MULTILINE).strip()
    for pat in [raw, None]:
        try:
            obj = json.loads(raw)
            if "action_type" in obj:
                return obj
        except Exception:
            break
    for pat in [r'\{[^{}]*"action_type"[^{}]*\}', r'\{.*?\}']:
        m = re.search(pat, raw, re.DOTALL)
        if m:
            try:
                obj = json.loads(m.group())
                if "action_type" in obj:
                    return obj
            except Exception:
                pass
    return {"action_type": "run_code"}

def run_task(task_id):
    print("[START] task=" + task_id, flush=True)
    rewards, steps, success = [], 0, False
    try:
        obs = requests.post(ENV_URL + "/reset", params={"task_id": task_id}, timeout=30).json()
        messages = [{"role": "system", "content": SYSTEM}]
        history = []
        for step_num in range(1, MAX_STEPS + 1):
            messages.append({"role": "user", "content": build_msg(obs, history)})
            try:
                raw = call_llm(messages)
            except Exception as e:
                print("[WARN] LLM: " + str(e), flush=True)
                raw = '{"action_type": "run_code"}'
            messages.append({"role": "assistant", "content": raw})
            action = parse_action(raw)
            atype  = action.get("action_type", "run_code")
            history.append(atype)
            result = requests.post(ENV_URL + "/step", json=action, timeout=30).json()
            reward = result.get("reward", 0.0)
            done   = result.get("done",   False)
            rewards.append(reward)
            steps = step_num
            print("[STEP] step=" + str(step_num) + " action=" + atype +
                  " reward=" + str(reward) + " done=" + str(done), flush=True)
            obs = result
            if done:
                tr = result.get("test_results", [])
                if tr:
                    p = sum(1 for t in tr if t["passed"])
                    print("[INFO] tests=" + str(p) + "/" + str(len(tr)), flush=True)
                    success = (p == len(tr))
                else:
                    success = reward >= 0.8
                break
    except Exception as e:
        print("[ERROR] task=" + task_id + " " + str(e), flush=True)
    score = rewards[-1] if rewards else 0.0
    print("[END] success=" + str(success) + " steps=" + str(steps) +
          " score=" + str(score) + " rewards=" + ",".join(str(r) for r in rewards), flush=True)
    return score

if __name__ == "__main__":
    total = sum(run_task(t) for t in TASKS)
    print("[END] average_score=" + str(round(total / len(TASKS), 4)), flush=True)
