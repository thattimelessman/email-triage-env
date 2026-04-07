import os
import json
import re
import requests
from openai import OpenAI

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama/Llama-3.3-70B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")
ENV_URL = os.getenv("ENV_URL", "http://localhost:7860")

client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

TASKS = ["easy", "medium", "hard"]

def run_task(task_id: str) -> float:
    print(f"[START] task={task_id}", flush=True)

    obs = requests.post(f"{ENV_URL}/reset", params={"task_id": task_id}).json()
    emails = obs["emails"]
    instructions = obs["instructions"]

    email_text = ""
    for e in emails:
        email_text += f"\nID: {e['id']}\nSubject: {e['subject']}\nFrom: {e['sender']}\nBody: {e['body']}\n---"

    prompt = f"""You are an email triage assistant.

Task: {instructions}

Emails:
{email_text}

For each email, respond with a JSON object with two keys:
- "classifications": a dict mapping each email ID to one of: urgent, normal, spam
- "departments": a dict mapping each email ID to the correct department (engineering, finance, hr, legal, security, product, spam)

Respond with ONLY the JSON object, no explanation."""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=500
    )

    raw = response.choices[0].message.content.strip()

    try:
        action = json.loads(raw)
    except Exception:
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        action = json.loads(match.group()) if match else {
            "classifications": {},
            "departments": {}
        }

    result = requests.post(f"{ENV_URL}/step", json=action).json()
    score = result["reward"]

    print(f"[STEP] step=1 reward={score}", flush=True)
    print(f"[END] task={task_id} score={score} steps=1", flush=True)

    return score

if __name__ == "__main__":
    total = 0
    for task in TASKS:
        score = run_task(task)
        total += score
    avg = round(total / len(TASKS), 4)
    print(f"[END] average_score={avg}", flush=True)