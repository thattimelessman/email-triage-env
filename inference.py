import os
from openai import OpenAI
import requests
import json

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama/Llama-3.3-70B-Instruct")
ENV_URL = os.getenv("ENV_URL", "http://localhost:7860")

client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

TASKS = ["easy", "medium", "hard"]

def run_task(task_id: str) -> float:
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
        import re
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        action = json.loads(match.group()) if match else {
            "classifications": {},
            "departments": {}
        }

    result = requests.post(f"{ENV_URL}/step", json=action).json()
    score = result["reward"]
    feedback = result["info"]["feedback"]
    print(f"Task: {task_id} | Score: {score} | {feedback}")
    return score

if __name__ == "__main__":
    print("Running Email Triage Baseline Inference\n")
    total = 0
    for task in TASKS:
        score = run_task(task)
        total += score
    avg = round(total / len(TASKS), 4)
    print(f"\nAverage Score: {avg}")