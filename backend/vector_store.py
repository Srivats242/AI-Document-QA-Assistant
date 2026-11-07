from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

DB_PATH = Path(__file__).resolve().parent / "chroma_db"

model = SentenceTransformer(MODEL_NAME)

client = chromadb.PersistentClient(path=str(DB_PATH))

collection = client.get_or_create_collection(
    name="document_chunks",
    metadata={"hnsw:space": "cosine"}
)


def store_document(document_id, filename, chunks):
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
            "page_number": chunk["page_number"]
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
