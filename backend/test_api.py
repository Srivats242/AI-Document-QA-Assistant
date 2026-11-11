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
mock_vector_store.list_documents = Mock()
mock_vector_store.get_document_info = Mock()
mock_vector_store.delete_document = Mock()
mock_vector_store.search_all_documents = Mock()
mock_vector_store.get_document_by_hash = Mock()

with patch.dict(sys.modules, {"vector_store": mock_vector_store}):
    import main


class TestAPI(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(main.app)


    def make_test_pdf(self):
        with main.pymupdf.open() as pdf:
            page = pdf.new_page()
            page.insert_text(
                (72, 72),
                "This is a sample PDF for testing."
            )
            return pdf.tobytes()

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


    def test_list_documents(self):
        documents = [
            {
                "document_id": "doc-123",
                "filename": "sample.pdf",
                "total_chunks": 10,
                "indexed_pages": 3
            }
        ]

        with patch.object(
            main, "list_documents", return_value=documents
        ):
            response = self.client.get("/documents")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(response.json()["documents"], documents)

    def test_get_document(self):
        document = {
            "document_id": "doc-123",
            "filename": "sample.pdf",
            "total_chunks": 10,
            "indexed_pages": 3
        }

        with patch.object(
            main, "get_document_info", return_value=document
        ):
            response = self.client.get("/documents/doc-123")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), document)

    def test_document_not_found(self):
        with patch.object(
            main, "get_document_info", return_value=None
        ):
            response = self.client.get("/documents/missing")

        self.assertEqual(response.status_code, 404)

    def test_delete_document(self):
        with patch.object(
            main, "delete_document", return_value=10
        ):
            response = self.client.delete("/documents/doc-123")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["deleted_chunks"], 10)

    def test_delete_missing_document(self):
        with patch.object(
            main, "delete_document", return_value=None
        ):
            response = self.client.delete("/documents/missing")

        self.assertEqual(response.status_code, 404)

    
    def test_search_all_documents(self):
        matches = [
            {
                "document_id": "doc-1",
                "filename": "Kim.pdf",
                "page_number": 3,
                "text": "Religion influences development.",
                "distance": 0.25
            },
            {
                "document_id": "doc-2",
                "filename": "sample.pdf",
                "page_number": 5,
                "text": "Development involves social change.",
                "distance": 0.35
            }
        ]

        with patch.object(
            main, "search_all_documents", return_value=matches
        ):
            response = self.client.post(
                "/search/all",
                json={
                    "question": "What is development?",
                    "limit": 5
                }
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total_matches"], 2)
        self.assertEqual(response.json()["matches"], matches)

    def test_search_all_no_matches(self):
        with patch.object(
            main, "search_all_documents", return_value=[]
        ):
            response = self.client.post(
                "/search/all",
                json={
                    "question": "What is development?",
                    "limit": 5
                }
            )

        self.assertEqual(response.status_code, 404)

    def test_search_all_empty_question(self):
        response = self.client.post(
            "/search/all",
            json={
                "question": "",
                "limit": 5
            }
        )

        self.assertEqual(response.status_code, 422)

    def test_search_all_invalid_limit(self):
        response = self.client.post(
            "/search/all",
            json={
                "question": "What is development?",
                "limit": 25
            }
        )

        self.assertEqual(response.status_code, 422)


    def test_upload_new_pdf(self):
        pdf_bytes = self.make_test_pdf()

        chunks = [
            {
                "text": "This is a sample PDF for testing.",
                "page_number": 1
            }
        ]

        with patch.object(
            main, "get_document_by_hash", return_value=None
        ), patch.object(
            main, "chunk_document", return_value=chunks
        ), patch.object(
            main, "store_document", return_value=1
        ) as mock_store:
            response = self.client.post(
                "/upload",
                files={
                    "file": (
                        "sample.pdf",
                        pdf_bytes,
                        "application/pdf"
                    )
                }
            )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["duplicate"])
        self.assertEqual(response.json()["total_chunks"], 1)

        mock_store.assert_called_once()

        import hashlib

        expected_hash = hashlib.sha256(pdf_bytes).hexdigest()

        self.assertEqual(
            mock_store.call_args.kwargs["file_hash"],
            expected_hash
        )

    def test_upload_duplicate_pdf(self):
        pdf_bytes = self.make_test_pdf()

        existing_document = {
            "document_id": "existing-doc-123",
            "filename": "sample.pdf",
            "total_chunks": 1,
            "indexed_pages": 1
        }

        with patch.object(
            main,
            "get_document_by_hash",
            return_value=existing_document
        ), patch.object(
            main, "store_document"
        ) as mock_store, patch.object(
            main, "chunk_document"
        ) as mock_chunk:
            response = self.client.post(
                "/upload",
                files={
                    "file": (
                        "sample.pdf",
                        pdf_bytes,
                        "application/pdf"
                    )
                }
            )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["duplicate"])
        self.assertEqual(
            response.json()["document_id"],
            "existing-doc-123"
        )

        mock_store.assert_not_called()
        mock_chunk.assert_not_called()

    def test_upload_same_pdf_twice(self):
        pdf_bytes = self.make_test_pdf()

        existing_document = {
            "document_id": "existing-doc-123",
            "filename": "sample.pdf",
            "total_chunks": 1,
            "indexed_pages": 1
        }

        with patch.object(
            main,
            "get_document_by_hash",
            side_effect=[None, existing_document]
        ), patch.object(
            main, "chunk_document",
            return_value=[{
                "text": "Sample text",
                "page_number": 1
            }]
        ), patch.object(
            main, "store_document",
            return_value=1
        ) as mock_store, patch.object(
            main, "uuid4",
            return_value="existing-doc-123"
        ):
            files = {
                "file": (
                    "sample.pdf",
                    pdf_bytes,
                    "application/pdf"
                )
            }

            first_response = self.client.post(
                "/upload", files=files
            )

            second_response = self.client.post(
                "/upload", files=files
            )

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)

        self.assertFalse(first_response.json()["duplicate"])
        self.assertTrue(second_response.json()["duplicate"])

        self.assertEqual(
            first_response.json()["document_id"],
            second_response.json()["document_id"]
        )

        mock_store.assert_called_once()

if __name__ == "__main__":
    unittest.main()
