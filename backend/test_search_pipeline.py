import unittest
from unittest.mock import MagicMock

from search_pipeline import run_search_pipeline


class TestSearchPipeline(unittest.TestCase):

    def setUp(self):
        self.collection = MagicMock()
        self.model = MagicMock()
        self.reranker = MagicMock()

        self.model.encode.return_value.tolist.return_value = [
            [0.1, 0.2, 0.3]
        ]

        self.collection.count.return_value = 30

        self.collection.query.return_value = {
            "documents": [[
                "First passage",
                "Second passage",
                "Third passage"
            ]],
            "metadatas": [[
                {
                    "document_id": "doc1",
                    "filename": "first.pdf",
                    "page_number": 1
                },
                {
                    "document_id": "doc2",
                    "filename": "second.pdf",
                    "page_number": 2
                },
                {
                    "document_id": "doc3",
                    "filename": "third.pdf",
                    "page_number": 3
                }
            ]],
            "distances": [[0.2, 0.3, 0.4]]
        }

        def fake_rerank(question, matches):
            scores = {
                "First passage": 1.0,
                "Second passage": 4.0,
                "Third passage": -1.0
            }

            ranked = [
                {
                    **match,
                    "relevance_score": scores[match["text"]]
                }
                for match in matches
            ]

            return sorted(
                ranked,
                key=lambda match: match["relevance_score"],
                reverse=True
            )

        self.reranker.side_effect = fake_rerank

    def search(self, question="Test question", limit=5):
        return run_search_pipeline(
            question=question,
            limit=limit,
            collection=self.collection,
            model=self.model,
            rerank_fn=self.reranker
        )

    def test_retrieves_extra_candidates(self):
        self.search()

        self.assertEqual(
            self.collection.query.call_args.kwargs["n_results"],
            20
        )

    def test_reranks_results(self):
        results = self.search()

        self.assertEqual(
            results[0]["text"],
            "Second passage"
        )
        self.assertEqual(
            results[1]["text"],
            "First passage"
        )

    def test_respects_result_limit(self):
        results = self.search(limit=2)

        self.assertEqual(len(results), 2)

    def test_preserves_document_metadata(self):
        results = self.search()

        self.assertEqual(results[0]["filename"], "second.pdf")
        self.assertEqual(results[0]["page_number"], 2)
        self.assertEqual(results[0]["document_id"], "doc2")

    def test_empty_question(self):
        results = self.search(question="   ")

        self.assertEqual(results, [])
        self.collection.query.assert_not_called()

    def test_empty_database(self):
        self.collection.count.return_value = 0

        results = self.search()

        self.assertEqual(results, [])
        self.reranker.assert_not_called()

    def test_invalid_limit(self):
        with self.assertRaises(ValueError):
            self.search(limit=0)

    def test_empty_query_results(self):
        self.collection.query.return_value = {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]]
        }

        results = self.search()

        self.assertEqual(results, [])
        self.reranker.assert_not_called()

    def test_mismatched_result_fields(self):
        self.collection.query.return_value = {
            "documents": [["First passage"]],
            "metadatas": [[]],
            "distances": [[0.2]]
        }

        with self.assertRaises(ValueError):
            self.search()

    def test_candidate_count_capped_at_database_size(self):
        self.collection.count.return_value = 2

        self.search()

        self.assertEqual(
            self.collection.query.call_args.kwargs["n_results"],
            2
        )


if __name__ == "__main__":
    unittest.main()
