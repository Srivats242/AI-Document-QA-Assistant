
import unittest
from unittest.mock import patch

from relevance_evaluator import rerank_matches


class TestRelevanceEvaluator(unittest.TestCase):

    @patch("relevance_evaluator.get_reranker")
    def test_ranks_by_relevance(self, mock_get_reranker):
        mock_get_reranker.return_value.predict.return_value = [
            0.5, 4.2, -1.0
        ]

        matches = [
            {"text": "Somewhat relevant"},
            {"text": "Highly relevant"},
            {"text": "Not relevant"},
        ]

        results = rerank_matches("Test question", matches)

        self.assertEqual(results[0]["text"], "Highly relevant")
        self.assertEqual(results[1]["text"], "Somewhat relevant")
        self.assertEqual(results[2]["text"], "Not relevant")
        self.assertEqual(results[0]["relevance_score"], 4.2)

    @patch("relevance_evaluator.get_reranker")
    def test_empty_matches(self, mock_get_reranker):
        results = rerank_matches("Test question", [])

        self.assertEqual(results, [])
        mock_get_reranker.assert_not_called()

    @patch("relevance_evaluator.get_reranker")
    def test_preserves_source_metadata(self, mock_get_reranker):
        mock_get_reranker.return_value.predict.return_value = [2.5]

        matches = [
            {
                "text": "Relevant passage",
                "filename": "example.pdf",
                "page_number": 3,
                "distance": 0.25,
            }
        ]

        results = rerank_matches("Test question", matches)

        self.assertEqual(results[0]["filename"], "example.pdf")
        self.assertEqual(results[0]["page_number"], 3)
        self.assertEqual(results[0]["distance"], 0.25)


if __name__ == "__main__":
    unittest.main()
