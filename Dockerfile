FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install fastapi uvicorn pydantic openai requests

EXPOSE 7860

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]