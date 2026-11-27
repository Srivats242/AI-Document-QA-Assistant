import hashlib
import tempfile
import unittest

from pathlib import Path
from unittest.mock import MagicMock, patch

import pymupdf

from evaluation.index_benchmark import (
    validate_document,
    extract_document_chunks,
    store_benchmark_chunks,
    index_documents
)


class TestBenchmarkIndexing(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.directory = Path(self.temp_dir.name)
        self.pdf_path = self.directory / "DOC001.pdf"

        with pymupdf.open() as document:
            page = document.new_page()
            page.insert_text(
                (72, 72),
                "This is a sample benchmark document."
            )
            document.save(self.pdf_path)

        self.entry = {
            "document_id": "DOC001",
            "title": "Sample Document",
            "filename": "DOC001.pdf",
            "total_pages": 1,
            "sha256": hashlib.sha256(
                self.pdf_path.read_bytes()
            ).hexdigest()
        }

        directory_patch = patch(
            "evaluation.index_benchmark.DOCUMENT_DIR",
            self.directory
        )

        directory_patch.start()
        self.addCleanup(directory_patch.stop)

        self.collection = MagicMock()
        self.model = MagicMock()

        self.collection.count.return_value = 0

        self.model.encode.return_value.tolist.return_value = [
            [0.1, 0.2, 0.3]
        ]

        self.chunks = [
            {
                "page_number": 1,
                "text": "Sample benchmark passage."
            }
        ]

    def test_validate_document(self):
        self.assertEqual(
            validate_document(self.entry),
            self.pdf_path
        )

    def test_missing_document(self):
        self.pdf_path.unlink()

        with self.assertRaises(FileNotFoundError):
            validate_document(self.entry)

    def test_document_hash_mismatch(self):
        entry = {
            **self.entry,
            "sha256": "invalid-hash"
        }

        with self.assertRaises(ValueError):
            validate_document(entry)

    def test_extract_document_chunks(self):
        chunks = extract_document_chunks(self.entry)

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]["page_number"], 1)
        self.assertIn(
            "sample benchmark document",
            chunks[0]["text"]
        )

    def test_page_count_mismatch(self):
        entry = {
            **self.entry,
            "total_pages": 2
        }

        with self.assertRaises(ValueError):
            extract_document_chunks(entry)

    def test_store_benchmark_chunks(self):
        count = store_benchmark_chunks(
            self.entry,
            self.chunks,
            self.collection,
            self.model
        )

        self.assertEqual(count, 1)

        arguments = self.collection.upsert.call_args.kwargs

        self.assertEqual(
            arguments["ids"],
            ["DOC001_chunk_0"]
        )

        self.assertEqual(
            arguments["metadatas"][0]["document_id"],
            "DOC001"
        )

        self.assertEqual(
            arguments["metadatas"][0]["page_number"],
            1
        )

    def test_batch_indexing(self):
        chunks = self.chunks * 3

        self.model.encode.side_effect = None

        with patch(
            "evaluation.index_benchmark.BATCH_SIZE", 2
        ):
            self.model.encode.return_value.tolist.side_effect = [
                [[0.1, 0.2, 0.3]] * 2,
                [[0.1, 0.2, 0.3]]
            ]

            count = store_benchmark_chunks(
                self.entry,
                chunks,
                self.collection,
                self.model
            )

        self.assertEqual(count, 3)
        self.assertEqual(
            self.collection.upsert.call_count, 2
        )

        last_batch = self.collection.upsert.call_args.kwargs

        self.assertEqual(
            last_batch["ids"],
            ["DOC001_chunk_2"]
        )

    def test_reject_nonempty_collection(self):
        self.collection.count.return_value = 10

        with self.assertRaises(ValueError):
            index_documents(
                [self.entry],
                self.collection,
                self.model,
                []
            )

    def test_reject_duplicate_document_ids(self):
        with self.assertRaises(ValueError):
            index_documents(
                [self.entry, self.entry],
                self.collection,
                self.model,
                []
            )

    def test_successful_indexing(self):
        self.collection.count.side_effect = [0, 1]

        report = index_documents(
            [self.entry],
            self.collection,
            self.model,
            []
        )

        self.assertEqual(report["total_documents"], 1)
        self.assertEqual(report["total_chunks"], 1)
        self.assertEqual(report["total_indexed_pages"], 1)

        self.assertEqual(
            report["document_id_map"],
            {"DOC001": "DOC001"}
        )

    def test_missing_required_page(self):
        questions = [{
            "relevant_sources": [{
                "document_id": "DOC001",
                "page_number": 5
            }]
        }]

        with self.assertRaises(ValueError):
            index_documents(
                [self.entry],
                self.collection,
                self.model,
                questions
            )

        self.collection.upsert.assert_not_called()

    def test_missing_required_document(self):
        questions = [{
            "relevant_sources": [{
                "document_id": "DOC999",
                "page_number": 1
            }]
        }]

        with self.assertRaises(ValueError):
            index_documents(
                [self.entry],
                self.collection,
                self.model,
                questions
            )

    def test_chunk_count_mismatch(self):
        self.collection.count.side_effect = [0, 2]

        with self.assertRaises(RuntimeError):
            index_documents(
                [self.entry],
                self.collection,
                self.model,
                []
            )


if __name__ == "__main__":
    unittest.main()
