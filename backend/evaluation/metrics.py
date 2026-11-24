import math


def _validate_k(k: int) -> None:
    """Ensure the retrieval cutoff is positive."""
    if k <= 0:
        raise ValueError("k must be greater than zero")


def _unique_results(retrieved: list[str]) -> list[str]:
    """Remove duplicate results while preserving ranking order."""
    return list(dict.fromkeys(retrieved))


def precision_at_k(
    retrieved: list[str],
    relevant: set[str],
    k: int = 5
) -> float:
    """Calculate the proportion of relevant results in the top k."""
    _validate_k(k)

    top_results = _unique_results(retrieved)[:k]

    relevant_count = sum(
        result in relevant for result in top_results
    )

    return relevant_count / k


def recall_at_k(
    retrieved: list[str],
    relevant: set[str],
    k: int = 5
) -> float:
    """Calculate the proportion of relevant results retrieved."""
    _validate_k(k)

    if not relevant:
        return 0.0

    top_results = _unique_results(retrieved)[:k]

    relevant_count = sum(
        result in relevant for result in top_results
    )

    return relevant_count / len(relevant)


def hit_rate_at_k(
    retrieved: list[str],
    relevant: set[str],
    k: int = 5
) -> float:
    """Return 1 if a relevant result appears in the top k."""
    _validate_k(k)

    top_results = _unique_results(retrieved)[:k]

    return float(
        any(result in relevant for result in top_results)
    )


def reciprocal_rank(
    retrieved: list[str],
    relevant: set[str]
) -> float:
    """Calculate the reciprocal rank of the first relevant result."""
    unique_results = _unique_results(retrieved)

    for rank, result in enumerate(unique_results, start=1):
        if result in relevant:
            return 1.0 / rank

    return 0.0


def mean_reciprocal_rank(
    rankings: list[list[str]],
    relevant_sets: list[set[str]]
) -> float:
    """Calculate mean reciprocal rank across multiple queries."""
    if len(rankings) != len(relevant_sets):
        raise ValueError(
            "Rankings and relevant sets must have equal lengths"
        )

    if not rankings:
        return 0.0

    scores = [
        reciprocal_rank(retrieved, relevant)
        for retrieved, relevant in zip(rankings, relevant_sets)
    ]

    return sum(scores) / len(scores)


def ndcg_at_k(
    retrieved: list[str],
    relevant: set[str],
    k: int = 5
) -> float:
    """Calculate normalized discounted cumulative gain."""
    _validate_k(k)

    if not relevant:
        return 0.0

    top_results = _unique_results(retrieved)[:k]

    dcg = sum(
        1.0 / math.log2(rank + 1)
        for rank, result in enumerate(top_results, start=1)
        if result in relevant
    )

    ideal_count = min(k, len(relevant))

    ideal_dcg = sum(
        1.0 / math.log2(rank + 1)
        for rank in range(1, ideal_count + 1)
    )

    return dcg / ideal_dcg


def evaluate_retrieval(
    retrieved: list[str],
    relevant: set[str],
    k: int = 5
) -> dict[str, float]:
    """Calculate retrieval evaluation metrics for a single query."""
    _validate_k(k)

    top_results = _unique_results(retrieved)[:k]

    return {
        f"precision@{k}": precision_at_k(retrieved, relevant, k),
        f"recall@{k}": recall_at_k(retrieved, relevant, k),
        f"hit_rate@{k}": hit_rate_at_k(retrieved, relevant, k),
        f"reciprocal_rank@{k}": reciprocal_rank(top_results, relevant),
        f"ndcg@{k}": ndcg_at_k(retrieved, relevant, k)
    }
