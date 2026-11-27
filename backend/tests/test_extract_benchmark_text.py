import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pymupdf

from evaluation import extract_benchmark_text as extractor


class TestBenchmarkExtraction(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.root = Path(self.temp_dir.name)
        self.documents = self.root / "documents"
        self.documents.mkdir()

        self.output = self.root / "extracted"
        self.manifest = self.root / "manifest.json"

        paths = {
            "DOCUMENT_DIR": self.documents,
            "OUTPUT_DIR": self.output,
            "MANIFEST_PATH": self.manifest
        }

        for name, value in paths.items():
            patcher = patch.object(extractor, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

        self.entry = {
            "document_id": "DOC001",
            "title": "Sample Benchmark Document",
            "category": "technical",
            "split": "development",
            "filename": "DOC001.pdf"
        }

        self.manifest.write_text(
            json.dumps([self.entry]),
            encoding="utf-8"
        )

    def create_pdf(self, texts):
        path = self.documents / self.entry["filename"]

        with pymupdf.open() as pdf:
            for text in texts:
                page = pdf.new_page()

                if text:
                    page.insert_text((50, 50), text)

            pdf.save(path)

        return path

    def create_scanned_pdf(self):
        path = self.documents / self.entry["filename"]

        with pymupdf.open() as original:
            page = original.new_page()
            page.insert_text((50, 50), "Scanned sample")
            image = page.get_pixmap()

            with pymupdf.open() as scanned:
                page = scanned.new_page()
                page.insert_image(page.rect, pixmap=image)
                scanned.save(path)

        return path

    def test_single_page_extraction(self):
        self.create_pdf(["Sample benchmark text"])

        result = extractor.extract_document(self.entry)

        self.assertEqual(result["total_pages"], 1)
        self.assertEqual(
            result["pages"][0]["text"],
            "Sample benchmark text"
        )
        self.assertEqual(
            result["pages"][0]["extraction_method"],
            "embedded"
        )

    def test_multipage_extraction(self):
        self.create_pdf([
            "First page",
            "Second page",
            "Third page"
        ])

        result = extractor.extract_document(self.entry)

        self.assertEqual(result["total_pages"], 3)

        self.assertEqual(
            [page["page_number"] for page in result["pages"]],
            [1, 2, 3]
        )

        self.assertEqual(
            result["pages"][2]["text"],
            "Third page"
        )

    def test_document_metadata(self):
        self.create_pdf(["Sample text"])

        result = extractor.extract_document(self.entry)

        for field in [
            "document_id",
            "title",
            "category",
            "split"
        ]:
            self.assertEqual(
                result[field],
                self.entry[field]
            )

    def test_ocr_fallback(self):
        self.create_scanned_pdf()

        with patch.object(
            pymupdf.Page,
            "get_textpage_ocr"
        ) as ocr, patch.object(
            pymupdf.Page,
            "get_text",
            side_effect=["", "Recognized scanned text"]
        ):
            result = extractor.extract_document(self.entry)

            ocr.assert_called_once()

        self.assertEqual(
            result["pages"][0]["extraction_method"],
            "ocr"
        )

        self.assertEqual(
            result["pages"][0]["text"],
            "Recognized scanned text"
        )

    def test_ocr_failure(self):
        self.create_scanned_pdf()

        with patch.object(
            pymupdf.Page,
            "get_textpage_ocr",
            side_effect=RuntimeError("Missing tessdata")
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "OCR failed for DOC001 on page 1"
            ):
                extractor.extract_document(self.entry)

    def test_json_export(self):
        self.create_pdf(["Exported benchmark text"])

        extractor.export_documents(["DOC001"])

        output_path = self.output / "DOC001.json"

        self.assertTrue(output_path.exists())

        result = json.loads(
            output_path.read_text(encoding="utf-8")
        )

        self.assertEqual(result["document_id"], "DOC001")
        self.assertEqual(result["total_pages"], 1)
        self.assertEqual(
            result["pages"][0]["text"],
            "Exported benchmark text"
        )

    def test_unknown_document_id(self):
        with self.assertRaisesRegex(
            ValueError,
            "Unknown document IDs"
        ):
            extractor.export_documents(["DOC999"])


if __name__ == "__main__":
    unittest.main()
