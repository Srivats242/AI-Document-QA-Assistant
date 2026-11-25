import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pymupdf

from evaluation import collect_documents as collector


class TestDocumentCollection(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.root = Path(self.temp_dir.name)
        self.documents = self.root / "documents"
        self.documents.mkdir()

        self.catalog = self.root / "catalog.json"
        self.manifest = self.root / "manifest.json"

        paths = {
            "DOCUMENT_DIR": self.documents,
            "CATALOG_PATH": self.catalog,
            "MANIFEST_PATH": self.manifest
        }

        for name, value in paths.items():
            patcher = patch.object(collector, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def create_pdf(self, filename, pages=1, text="Sample text"):
        path = self.documents / filename

        with pymupdf.open() as pdf:
            for _ in range(pages):
                page = pdf.new_page()
                page.insert_text((50, 50), text)

            pdf.save(path)

        return path

    def create_catalog(self, document_ids):
        entries = []

        for document_id in document_ids:
            entries.append({
                "document_id": document_id,
                "title": f"Test Document {document_id}",
                "publisher": "Test Publisher",
                "category": "technical",
                "split": "test",
                "filename": f"{document_id}.pdf",
                "source_url": "https://example.com/test.pdf"
            })

        self.catalog.write_text(
            json.dumps(entries),
            encoding="utf-8"
        )

    def test_inspect_valid_pdf(self):
        path = self.create_pdf("valid.pdf")

        metadata = collector.inspect_pdf(path)

        self.assertEqual(metadata["total_pages"], 1)
        self.assertEqual(
            metadata["pages_with_embedded_text"], 1
        )
        self.assertEqual(
            metadata["pages_without_embedded_text"], 0
        )
        self.assertGreater(metadata["file_size_bytes"], 0)

    def test_inspect_multipage_pdf(self):
        path = self.create_pdf("multiple.pdf", pages=3)

        metadata = collector.inspect_pdf(path)

        self.assertEqual(metadata["total_pages"], 3)
        self.assertEqual(
            metadata["pages_with_embedded_text"], 3
        )

    def test_reject_invalid_pdf(self):
        path = self.documents / "invalid.pdf"
        path.write_bytes(b"This is not a PDF")

        with self.assertRaises(ValueError):
            collector.inspect_pdf(path)

    def test_inspect_image_only_pdf(self):
        path = self.documents / "scanned.pdf"

        with pymupdf.open() as original:
            page = original.new_page()
            page.insert_text((50, 50), "Scanned text")
            image = page.get_pixmap()

            with pymupdf.open() as scanned:
                scanned_page = scanned.new_page()
                scanned_page.insert_image(
                    scanned_page.rect,
                    pixmap=image
                )
                scanned.save(path)

        metadata = collector.inspect_pdf(path)

        self.assertEqual(metadata["total_pages"], 1)
        self.assertEqual(
            metadata["pages_with_embedded_text"], 0
        )
        self.assertEqual(
            metadata["pages_without_embedded_text"], 1
        )

    def test_sha256_hash(self):
        path = self.create_pdf("hash.pdf")

        expected = hashlib.sha256(
            path.read_bytes()
        ).hexdigest()

        metadata = collector.inspect_pdf(path)

        self.assertEqual(metadata["sha256"], expected)

    def test_successful_collection(self):
        self.create_catalog(["DOC001"])
        self.create_pdf("DOC001.pdf")

        with patch.object(collector, "download_pdf") as download:
            collector.collect_documents()
            download.assert_not_called()

        self.assertTrue(self.manifest.exists())

        records = json.loads(
            self.manifest.read_text(encoding="utf-8")
        )

        self.assertEqual(len(records), 1)
        self.assertEqual(
            records[0]["document_id"], "DOC001"
        )
        self.assertEqual(records[0]["total_pages"], 1)

    def test_reject_duplicate_documents(self):
        self.create_catalog(["DOC001", "DOC002"])

        first = self.create_pdf("DOC001.pdf")
        second = self.documents / "DOC002.pdf"

        second.write_bytes(first.read_bytes())

        with self.assertRaises(SystemExit):
            collector.collect_documents()

        self.assertFalse(self.manifest.exists())

    def test_reject_changed_document(self):
        self.create_catalog(["DOC001"])

        path = self.create_pdf("DOC001.pdf")
        collector.collect_documents()

        original_manifest = self.manifest.read_bytes()

        path.unlink()
        self.create_pdf("DOC001.pdf", text="Modified content")

        with self.assertRaises(SystemExit):
            collector.collect_documents()

        self.assertEqual(
            self.manifest.read_bytes(),
            original_manifest
        )

    def test_failed_collection_preserves_manifest(self):
        self.create_catalog(["DOC001"])
        self.create_pdf("DOC001.pdf")

        collector.collect_documents()

        original_manifest = self.manifest.read_bytes()

        self.create_catalog(["DOC001", "DOC002"])

        with patch.object(
            collector,
            "download_pdf",
            side_effect=RuntimeError("Download failed")
        ):
            with self.assertRaises(SystemExit):
                collector.collect_documents()

        self.assertEqual(
            self.manifest.read_bytes(),
            original_manifest
        )


if __name__ == "__main__":
    unittest.main()
