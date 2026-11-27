from search_pipeline import run_search_pipeline


VALID_STRATEGIES = {
    "vector",
    "reranked",
    "full"
}


def preserve_vector_order(question, matches):
    return matches


def create_retriever(
    collection,
    model,
    strategy="full",
    rerank_fn=None
):
    if strategy not in VALID_STRATEGIES:
        raise ValueError(
            f"Unknown retrieval strategy: {strategy}"
        )

    if strategy == "vector":
        ranking_function = preserve_vector_order
    else:
        if rerank_fn is None:
            from relevance_evaluator import rerank_matches
            rerank_fn = rerank_matches

        ranking_function = rerank_fn

    def retrieve(question, k=5):
        return run_search_pipeline(
            question=question,
            limit=k,
            collection=collection,
            model=model,
            rerank_fn=ranking_function,
            apply_source_quality=(strategy == "full"),
            unique_pages=True
        )

    return retrieve
