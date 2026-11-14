def run_search_pipeline(
    question,
    limit,
    collection,
    model,
    rerank_fn
):
    if not question.strip():
        return []

    if limit < 1:
        raise ValueError("Limit must be positive")

    total_chunks = collection.count()

    if total_chunks == 0:
        return []

    question_embedding = model.encode(
        [question],
        normalize_embeddings=True
    ).tolist()

    candidate_count = min(
        max(limit * 4, 20),
        total_chunks
    )

    results = collection.query(
        query_embeddings=question_embedding,
        n_results=candidate_count,
        include=["documents", "metadatas", "distances"]
    )

    documents = results.get("documents") or [[]]
    metadatas = results.get("metadatas") or [[]]
    distances = results.get("distances") or [[]]

    texts = documents[0]
    metadata_list = metadatas[0]
    distance_list = distances[0]

    if not (
        len(texts)
        == len(metadata_list)
        == len(distance_list)
    ):
        raise ValueError("Search result fields have mismatched lengths")

    matches = []

    for text, metadata, distance in zip(
        texts,
        metadata_list,
        distance_list
    ):
        matches.append({
            "document_id": metadata["document_id"],
            "filename": metadata["filename"],
            "page_number": metadata["page_number"],
            "text": text,
            "distance": distance
        })

    if not matches:
        return []

    ranked_matches = rerank_fn(question, matches)

    return ranked_matches[:limit]
