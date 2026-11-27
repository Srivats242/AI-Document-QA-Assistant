from source_quality import rerank_for_source_quality
def run_search_pipeline(
    question,
    limit,
    collection,
    model,
    rerank_fn,
    *,
    apply_source_quality=True,
    unique_pages=False
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

    if apply_source_quality:
        ranked_matches = rerank_for_source_quality(
            question,
            ranked_matches
        )

    if unique_pages:
        seen_pages = set()
        unique_matches = []

        for match in ranked_matches:
            page_key = (
                match["document_id"],
                match["page_number"]
            )

            if page_key not in seen_pages:
                seen_pages.add(page_key)
                unique_matches.append(match)

        ranked_matches = unique_matches

    return ranked_matches[:limit]
