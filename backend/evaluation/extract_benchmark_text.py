import argparse
import json
from pathlib import Path

import pymupdf


DATASET_DIR = Path(__file__).resolve().parent / "datasets"
DOCUMENT_DIR = DATASET_DIR / "documents"
MANIFEST_PATH = DATASET_DIR / "manifest.json"
OUTPUT_DIR = DATASET_DIR / "extracted"


def extract_document(entry):
    path = DOCUMENT_DIR / entry["filename"]
    pages = []

    with pymupdf.open(path) as document:
        for page_number, page in enumerate(document, start=1):
            text = page.get_text().strip()
            extraction_method = "embedded"

            if not text:
                try:
                    text_page = page.get_textpage_ocr(
                        language="eng",
                        dpi=200,
                        full=True
                    )
                except RuntimeError as error:
                    raise RuntimeError(
                        f"OCR failed for {entry['document_id']} "
                        f"on page {page_number}. Verify Tesseract "
                        "and the TESSDATA_PREFIX environment variable."
                    ) from error

                text = page.get_text(
                    textpage=text_page
                ).strip()

                extraction_method = "ocr"

            pages.append({
                "page_number": page_number,
                "extraction_method": extraction_method,
                "text": text
            })

    return {
        "document_id": entry["document_id"],
        "title": entry["title"],
        "category": entry["category"],
        "split": entry["split"],
        "total_pages": len(pages),
        "pages": pages
    }


def export_documents(document_ids):
    manifest = json.loads(
        MANIFEST_PATH.read_text(encoding="utf-8-sig")
    )

    available_ids = {
        entry["document_id"] for entry in manifest
    }

    unknown_ids = set(document_ids) - available_ids

    if unknown_ids:
        raise ValueError(
            f"Unknown document IDs: {sorted(unknown_ids)}"
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for entry in manifest:
        if entry["document_id"] not in document_ids:
            continue

        document_id = entry["document_id"]

        print(f"Extracting {document_id}: {entry['title']}")

        result = extract_document(entry)

        output_path = OUTPUT_DIR / f"{document_id}.json"

        output_path.write_text(
            json.dumps(
                result,
                indent=4,
                ensure_ascii=False
            ),
            encoding="utf-8"
        )

        ocr_pages = sum(
            page["extraction_method"] == "ocr"
            for page in result["pages"]
        )

        print(f"Pages extracted: {result['total_pages']}")
        print(f"OCR pages: {ocr_pages}")
        print(f"Saved to: {output_path}")
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract benchmark document text"
    )

    parser.add_argument(
        "document_ids",
        nargs="+",
        help="Document IDs to extract"
    )

    args = parser.parse_args()

    export_documents(args.document_ids)
