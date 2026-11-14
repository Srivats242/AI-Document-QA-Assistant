from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer
from relevance_evaluator import rerank_matches
from search_pipeline import run_search_pipeline

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

DB_PATH = Path(__file__).resolve().parent / "chroma_db"

model = SentenceTransformer(MODEL_NAME)

client = chromadb.PersistentClient(path=str(DB_PATH))

collection = client.get_or_create_collection(
    name="document_chunks",
    metadata={"hnsw:space": "cosine"}
)


def store_document(document_id, filename, chunks, file_hash=None):
    if not chunks:
        return 0

    texts = [chunk["text"] for chunk in chunks]

    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=False
    ).tolist()

    ids = [
        f"{document_id}_chunk_{i}"
        for i in range(len(chunks))
    ]

    metadatas = [
        {
            "document_id": document_id,
            "filename": filename,
            "page_number": chunk["page_number"],
            **({"file_hash": file_hash} if file_hash else {})
        }
        for chunk in chunks
    ]

    collection.upsert(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas
    )

    return len(chunks)


def search_document(document_id, question, limit=5):
    if not question.strip():
        return []

    question_embedding = model.encode(
        [question],
        normalize_embeddings=True
    ).tolist()

    results = collection.query(
        query_embeddings=question_embedding,
        n_results=limit,
        where={"document_id": document_id}
    )

    matches = []

    for i, text in enumerate(results["documents"][0]):
        matches.append({
            "text": text,
            "page_number": results["metadatas"][0][i]["page_number"],
            "distance": results["distances"][0][i]
        })

    return matches


def get_document_records(document_id=None):
    records = []
    offset = 0
    batch_size = 500

    while True:
        options = {
            "include": ["metadatas"],
            "limit": batch_size,
            "offset": offset
        }

        if document_id is not None:
            options["where"] = {"document_id": document_id}

        results = collection.get(**options)

        ids = results["ids"]
        metadatas = results["metadatas"]

        for chunk_id, metadata in zip(ids, metadatas):
            records.append({
                "chunk_id": chunk_id,
                "metadata": metadata
            })

        if len(ids) < batch_size:
            break

        offset += batch_size

    return records


def list_documents():
    documents = {}

    for record in get_document_records():
        metadata = record["metadata"]
        document_id = metadata["document_id"]

        if document_id not in documents:
            documents[document_id] = {
                "document_id": document_id,
                "filename": metadata["filename"],
                "total_chunks": 0,
                "page_numbers": set()
            }

        documents[document_id]["total_chunks"] += 1
        documents[document_id]["page_numbers"].add(
            metadata["page_number"]
        )

    result = []

    for document in documents.values():
        document["indexed_pages"] = len(
            document.pop("page_numbers")
        )
        result.append(document)

    return sorted(result, key=lambda item: item["filename"])


def get_document_info(document_id):
    records = get_document_records(document_id)

    if not records:
        return None

    metadata = records[0]["metadata"]

    return {
        "document_id": document_id,
        "filename": metadata["filename"],
        "total_chunks": len(records),
        "indexed_pages": len({
            record["metadata"]["page_number"]
            for record in records
        })
    }


def delete_document(document_id):
    document = get_document_info(document_id)

    if document is None:
        return None

    collection.delete(
        where={"document_id": document_id}
    )

    return document["total_chunks"]

def search_all_documents(question, limit=5):
    return run_search_pipeline(
        question=question,
        limit=limit,
        collection=collection,
        model=model,
        rerank_fn=rerank_matches
    )

def get_document_by_hash(file_hash):
    results = collection.get(
        where={"file_hash": file_hash},
        include=["metadatas"],
        limit=1
    )

    if not results["ids"]:
        return None

    document_id = results["metadatas"][0]["document_id"]

    return get_document_info(document_id)


def get_document_stats():
    documents = list_documents()

    total_documents = len(documents)

    total_chunks = sum(
        document["total_chunks"]
        for document in documents
    )

    total_indexed_pages = sum(
        document["indexed_pages"]
        for document in documents
    )

    return {
        "total_documents": total_documents,
        "total_chunks": total_chunks,
        "total_indexed_pages": total_indexed_pages
    }



