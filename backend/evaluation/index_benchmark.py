import hashlib
import json
from pathlib import Path

import pymupdf

from document_processor import chunk_document
from pdf_extractor import extract_page_text
from evaluation.dataset import load_dataset


EVALUATION_DIR = Path(__file__).resolve().parent
DATASET_DIR = EVALUATION_DIR / "datasets"
DOCUMENT_DIR = DATASET_DIR / "documents"
MANIFEST_PATH = DATASET_DIR / "manifest.json"
BENCHMARK_PATH = DATASET_DIR / "benchmark.json"
DB_PATH = EVALUATION_DIR / "benchmark_db"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
COLLECTION_NAME = "benchmark_chunks"
BATCH_SIZE = 128


def load_manifest():
    with MANIFEST_PATH.open(
        "r", encoding="utf-8-sig"
    ) as file:
        return json.load(file)


def validate_document(entry):
    path = DOCUMENT_DIR / entry["filename"]

    if not path.is_file():
        raise FileNotFoundError(path)

    file_hash = hashlib.sha256(
        path.read_bytes()
    ).hexdigest()

    if file_hash != entry["sha256"]:
        raise ValueError(
            f"Document hash mismatch: {entry['document_id']}"
        )

    return path


def extract_document_chunks(entry):
    path = validate_document(entry)
    pages = []

    with pymupdf.open(path) as document:
        if document.needs_pass:
            raise ValueError("Password-protected PDF")

        if len(document) != entry["total_pages"]:
            raise ValueError(
                f"Page count mismatch: {entry['document_id']}"
            )

        for page_number, page in enumerate(document, start=1):
            pages.append({
                "page_number": page_number,
                "text": extract_page_text(page)
            })

    chunks = chunk_document(pages)

    if not chunks:
        raise ValueError(
            f"No extractable chunks: {entry['document_id']}"
        )

    return chunks


def store_benchmark_chunks(entry, chunks, collection, model):
    document_id = entry["document_id"]

    for start in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[start:start + BATCH_SIZE]

        texts = [chunk["text"] for chunk in batch]

        embeddings = model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False
        ).tolist()

        ids = [
            f"{document_id}_chunk_{start + i}"
            for i in range(len(batch))
        ]

        metadatas = [
            {
                "document_id": document_id,
                "filename": entry["filename"],
                "page_number": chunk["page_number"],
                "file_hash": entry["sha256"]
            }
            for chunk in batch
        ]

        collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )

    return len(chunks)


def index_documents(manifest, collection, model, questions):
    if collection.count() != 0:
        raise ValueError(
            "Benchmark collection must be empty before indexing"
        )

    document_ids = [
        entry["document_id"] for entry in manifest
    ]

    if len(document_ids) != len(set(document_ids)):
        raise ValueError("Duplicate benchmark document IDs")

    for entry in manifest:
        validate_document(entry)

    required_pages = {}

    for question in questions:
        for source in question["relevant_sources"]:
            document_id = source["document_id"]

            if document_id not in document_ids:
                raise ValueError(
                    f"Missing benchmark document: {document_id}"
                )

            required_pages.setdefault(
                document_id, set()
            ).add(source["page_number"])

    documents = []
    total_chunks = 0

    for entry in manifest:
        document_id = entry["document_id"]

        print(f"\nIndexing {document_id}: {entry['title']}")

        chunks = extract_document_chunks(entry)

        indexed_pages = {
            chunk["page_number"] for chunk in chunks
        }

        missing_pages = (
            required_pages.get(document_id, set())
            - indexed_pages
        )

        if missing_pages:
            raise ValueError(
                f"{document_id} is missing required pages: "
                f"{sorted(missing_pages)}"
            )

        stored_count = store_benchmark_chunks(
            entry, chunks, collection, model
        )

        documents.append({
            "document_id": document_id,
            "total_pages": entry["total_pages"],
            "indexed_pages": len(indexed_pages),
            "total_chunks": stored_count
        })

        total_chunks += stored_count

        print(f"Indexed pages: {len(indexed_pages)}")
        print(f"Stored chunks: {stored_count}")

    if collection.count() != total_chunks:
        raise RuntimeError("Stored chunk count mismatch")

    return {
        "model": MODEL_NAME,
        "total_documents": len(documents),
        "total_chunks": total_chunks,
        "total_indexed_pages": sum(
            document["indexed_pages"]
            for document in documents
        ),
        "document_id_map": {
            document_id: document_id
            for document_id in document_ids
        },
        "documents": documents
    }


def main():
    import chromadb
    from sentence_transformers import SentenceTransformer

    manifest = load_manifest()
    questions = load_dataset(BENCHMARK_PATH)

    client = chromadb.PersistentClient(path=str(DB_PATH))

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    if collection.count() != 0:
        raise SystemExit(
            "Benchmark database already contains chunks. "
            "Use the existing index or move the benchmark "
            "database folder before rebuilding."
        )

    model = SentenceTransformer(MODEL_NAME)

    report = index_documents(
        manifest, collection, model, questions
    )

    report_path = DB_PATH / "index_summary.json"

    report_path.write_text(
        json.dumps(report, indent=4),
        encoding="utf-8"
    )

    print("\nBenchmark indexing complete")
    print("-" * 40)
    print(f"Documents: {report['total_documents']}")
    print(f"Chunks: {report['total_chunks']}")
    print(f"Indexed pages: {report['total_indexed_pages']}")
    print(f"Summary saved to: {report_path}")


if __name__ == "__main__":
    main()
