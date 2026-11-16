import os

from openai import OpenAI

from rag_prompt import build_rag_prompt


def generate_answer(
    question: str,
    matches: list[dict],
    client=None,
    model: str | None = None,
) -> str:
    """Generate an answer using retrieved document passages."""

    prompt = build_rag_prompt(question, matches)

    if client is None:
        client = OpenAI()

    selected_model = model or os.getenv(
        "OPENAI_MODEL", "gpt-4.1-mini"
    )

    response = client.responses.create(
        model=selected_model,
        input=prompt,
        store=False,
    )

    answer = (response.output_text or "").strip()

    if not answer:
        raise ValueError("The AI model returned an empty answer.")

    return answer
