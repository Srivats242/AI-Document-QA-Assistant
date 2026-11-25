import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen
from collections import Counter

import pymupdf


DATASET_DIR = Path(__file__).resolve().parent / "datasets"
DOCUMENT_DIR = DATASET_DIR / "documents"
CATALOG_PATH = DATASET_DIR / "catalog.json"
MANIFEST_PATH = DATASET_DIR / "manifest.json"


def download_pdf(url: str, destination: Path) -> None:
    """Download a PDF from its original source."""
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    with urlopen(request, timeout=60) as response:
        content = response.read()

    if not content.startswith(b"%PDF-"):
        raise ValueError("Downloaded file is not a valid PDF")

    destination.write_bytes(content)


def inspect_pdf(path: Path) -> dict:
    """Collect reproducibility and document metadata."""
    content = path.read_bytes()

    if not content.startswith(b"%PDF-"):
        raise ValueError("Invalid PDF header")

    with pymupdf.open(path) as document:
        if document.needs_pass:
            raise ValueError("Password-protected PDF")

        page_count = len(document)

        if page_count == 0:
            raise ValueError("PDF contains no pages")

        pages_with_text = sum(
            bool(page.get_text().strip())
            for page in document
        )

    return {
        "sha256": hashlib.sha256(content).hexdigest(),
        "file_size_bytes": len(content),
        "total_pages": page_count,
        "pages_with_embedded_text": pages_with_text,
        "pages_without_embedded_text": (
            page_count - pages_with_text
        )
    }


def collect_documents() -> list[dict]:
    """Download and inspect all documents in the catalog."""
    DOCUMENT_DIR.mkdir(parents=True, exist_ok=True)

    with CATALOG_PATH.open(
        "r", encoding="utf-8-sig"
    ) as file:
        catalog = json.load(file)

    manifest = []
    failures = []
    seen_hashes = set()

    previous_manifest = {}

    if MANIFEST_PATH.exists():
        previous_manifest = {
            item["document_id"]: item
            for item in json.loads(
                MANIFEST_PATH.read_text(encoding="utf-8-sig")
            )
        }

    for entry in catalog:
        document_id = entry["document_id"]
        destination = DOCUMENT_DIR / entry["filename"]

        print(f"\nProcessing {document_id}:")
        print(entry["title"])

        try:
            if not destination.exists():
                if entry.get("manual_download"):
                    raise ValueError(
                        "Manual download required. "
                        f"Save PDF as {destination.name}"
                    )

                download_pdf(
                    entry["source_url"],
                    destination
                )

                print("Download completed.")
            else:
                print("Using existing PDF.")

            metadata = inspect_pdf(destination)

            previous = previous_manifest.get(document_id)

            if previous and (
                previous["sha256"] != metadata["sha256"]
            ):
                raise ValueError(
                    "PDF differs from previously recorded version"
                )

            if metadata["sha256"] in seen_hashes:
                raise ValueError("Duplicate PDF content")

            seen_hashes.add(metadata["sha256"])

            record = {
                **entry,
                **metadata
            }

            manifest.append(record)

            print(f"Pages: {metadata['total_pages']}")
            print(f"SHA-256: {metadata['sha256']}")
            print("Validation passed.")

        except Exception as error:
            failures.append(document_id)
            print(f"Failed: {error}")

    if failures:
        print("\nFailed documents:", ", ".join(failures))
        print("Manifest not updated. Resolve failures and rerun.")
        raise SystemExit(1)

    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=4),
        encoding="utf-8"
    )

    print("\nCollection summary")
    print("-" * 40)
    print(f"Documents: {len(manifest)}")

    print(
        "Total pages:",
        sum(item["total_pages"] for item in manifest)
    )

    print(
        "Categories:",
        dict(Counter(item["category"] for item in manifest))
    )

    print(
        "Splits:",
        dict(Counter(item["split"] for item in manifest))
    )

    print(f"Manifest saved to: {MANIFEST_PATH}")

    return manifest


if __name__ == "__main__":
    collect_documents()
