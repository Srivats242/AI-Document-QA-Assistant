from functools import lru_cache

from sentence_transformers import CrossEncoder

RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

@lru_cache(maxsize=1)
def get_reranker():
    # Load the model only when relevance evaluation is needed.
    return CrossEncoder(RERANKER_MODEL)

def rerank_matches(question, matches):
    if not matches:
        return []

    # Evaluate each question and passage together.
    pairs = [
        (question, match["text"])
        for match in matches
    ]

    scores = get_reranker().predict(
        pairs,
        show_progress_bar=False
    )

    ranked_matches = []

    for match, score in zip(matches, scores):
        ranked_matches.append({
            **match,
            "relevance_score": float(score)
        })

    # Higher Cross-Encoder scores indicate stronger relevance.
    ranked_matches.sort(
        key=lambda match: match["relevance_score"],
        reverse=True
    )

    return ranked_matches