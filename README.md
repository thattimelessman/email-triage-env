---
title: Email Triage Env
emoji: 📧
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
tags:
  - openenv
---

# Email Triage Environment

An OpenEnv environment where an AI agent triages emails by classifying them and assigning them to the correct department.

## Tasks
| Task | Difficulty | Description |
|------|-----------|-------------|
| easy | Easy | Classify 1 email |
| medium | Medium | Classify 5 emails + assign departments |
| hard | Hard | Classify 10 emails + assign departments + detect phishing |

## Setup
pip install fastapi uvicorn pydantic openai
uvicorn main:app --host 0.0.0.0 --port 7860

## Environment Variables
- API_BASE_URL
- MODEL_NAME
- HF_TOKEN