import sys
import unittest
from types import ModuleType
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient


# Mock the vector database so tests don't load
# embedding models or use the actual database.
mock_vector_store = ModuleType("vector_store")
mock_vector_store.store_document = Mock()
mock_vector_store.search_document = Mock()

with patch.dict(sys.modules, {"vector_store": mock_vector_store}):
    import main


class TestAPI(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(main.app)

    def test_home(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.json())

    def test_health(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "healthy"}
        )

    def test_missing_document(self):
        data = {
            "document_id": "nonexistent-document",
            "question": "What is this document about?",
            "limit": 3
        }

        with patch.object(main, "search_document", return_value=[]):
            response = self.client.post("/search", json=data)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["detail"],
            "No indexed passages found for this document"
        )

    def test_valid_search(self):
        data = {
            "document_id": "test-document",
            "question": "What is artificial intelligence?",
            "limit": 3
        }

        matches = [
            {
                "text": "Artificial intelligence is a field of computing.",
                "page_number": 1,
                "filename": "test.pdf",
                "distance": 0.2
            }
        ]

        with patch.object(
            main, "search_document", return_value=matches
        ):
            response = self.client.post("/search", json=data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["matches"], matches)

    def test_empty_question(self):
        data = {
            "document_id": "test-document",
            "question": "",
            "limit": 3
        }

        response = self.client.post("/search", json=data)

        self.assertEqual(response.status_code, 422)

    def test_invalid_limit(self):
        data = {
            "document_id": "test-document",
            "question": "What is this about?",
            "limit": 0
        }

        response = self.client.post("/search", json=data)

        self.assertEqual(response.status_code, 422)

    def test_invalid_file_type(self):
        files = {
            "file": ("notes.txt", b"Hello world", "text/plain")
        }

        response = self.client.post("/upload", files=files)

        self.assertEqual(response.status_code, 400)

    def test_invalid_pdf_content(self):
        files = {
            "file": ("invalid.pdf", b"Not a PDF", "application/pdf")
        }

        response = self.client.post("/upload", files=files)

        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
