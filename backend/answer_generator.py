import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq
from rag_prompt import build_rag_prompt

# Automatically load GroqCloud credentials from backend/.env
load_dotenv(Path(__file__).resolve().parent / ".env")


def generate_answer(
    question: str,
    matches: list[dict],
    client=None,
    model: str | None = None,
) -> str:
    prompt = build_rag_prompt(question, matches)

    if client is None:
        client = Groq()

    selected_model = model or os.getenv(
        "GROQ_MODEL",
        "openai/gpt-oss-20b",
    )

    response = client.chat.completions.create(
        model=selected_model,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0,
    )

    answer = (
        response.choices[0].message.content or ""
    ).strip()

    if not answer:
        raise ValueError(
            "The AI model returned an empty answer."
        )

    return answer
