import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from groq import GroqError

from main import app


class TestAskAPI(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

        self.matches = [
            {
                "document_id": "doc-123",
                "filename": "Kim.pdf",
                "page_number": 4,
                "text": "Missionaries established schools.",
                "distance": 0.25,
                "relevance_score": 0.92,
            }
        ]

    @patch("main.generate_answer")
    @patch("main.search_all_documents")
    def test_successful_answer(self, mock_search, mock_generate):
        mock_search.return_value = self.matches
        mock_generate.return_value = (
            "Missionaries established schools [1]."
        )

        response = self.client.post(
            "/ask",
            json={
                "question": "What did missionaries establish?",
                "limit": 5
            }
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(
            data["answer"],
            "Missionaries established schools [1]."
        )
        self.assertEqual(data["total_sources"], 1)
        self.assertEqual(data["sources"][0]["citation"], "[1]")
        self.assertEqual(data["sources"][0]["filename"], "Kim.pdf")

        mock_search.assert_called_once_with(
            question="What did missionaries establish?",
            limit=5
        )
        mock_generate.assert_called_once_with(
            question="What did missionaries establish?",
            matches=self.matches
        )

    @patch("main.generate_answer")
    @patch("main.search_all_documents")
    def test_no_search_results(self, mock_search, mock_generate):
        mock_search.return_value = []

        response = self.client.post(
            "/ask",
            json={"question": "What happened?"}
        )

        self.assertEqual(response.status_code, 404)
        mock_generate.assert_not_called()

    def test_empty_question(self):
        response = self.client.post(
            "/ask",
            json={"question": ""}
        )

        self.assertEqual(response.status_code, 422)

    def test_invalid_limit(self):
        response = self.client.post(
            "/ask",
            json={
                "question": "What happened?",
                "limit": 0
            }
        )

        self.assertEqual(response.status_code, 422)

    @patch("main.generate_answer")
    @patch("main.search_all_documents")
    def test_ai_generation_failure(self, mock_search, mock_generate):
        mock_search.return_value = self.matches
        mock_generate.side_effect = GroqError(
            "Model unavailable"
        )

        response = self.client.post(
            "/ask",
            json={"question": "What happened?"}
        )

        self.assertEqual(response.status_code, 502)


if __name__ == "__main__":
    unittest.main()
