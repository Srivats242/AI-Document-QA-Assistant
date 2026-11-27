import unittest
from unittest.mock import MagicMock

from evaluation.retrieval import create_retriever


class TestBenchmarkRetrieval(unittest.TestCase):

    def setUp(self):
        self.collection = MagicMock()
        self.model = MagicMock()
        self.reranker = MagicMock()

        self.collection.count.return_value = 30

        self.model.encode.return_value.tolist.return_value = [
            [0.1, 0.2, 0.3]
        ]

        self.collection.query.return_value = {
            "documents": [[
                "Normal passage",
                "Another passage from the same page",
                "Journal 2001 Press 2002 Publisher 2003",
                "Relevant technical passage"
            ]],
            "metadatas": [[
                {
                    "document_id": "DOC001",
                    "filename": "DOC001.pdf",
                    "page_number": 1
                },
                {
                    "document_id": "DOC001",
                    "filename": "DOC001.pdf",
                    "page_number": 1
                },
                {
                    "document_id": "DOC002",
                    "filename": "DOC002.pdf",
                    "page_number": 2
                },
                {
                    "document_id": "DOC003",
                    "filename": "DOC003.pdf",
                    "page_number": 3
                }
            ]],
            "distances": [[0.1, 0.2, 0.3, 0.4]]
        }

        def fake_rerank(question, matches):
            scores = [1.0, 0.5, 5.0, 4.0]

            ranked = [
                {
                    **match,
                    "relevance_score": score
                }
                for match, score in zip(matches, scores)
            ]

            return sorted(
                ranked,
                key=lambda item: item["relevance_score"],
                reverse=True
            )

        self.reranker.side_effect = fake_rerank

    def retrieve(self, strategy, k=3):
        retrieve_fn = create_retriever(
            self.collection,
            self.model,
            strategy=strategy,
            rerank_fn=self.reranker
        )

        return retrieve_fn("Explain the main topic", k)

    def test_vector_strategy(self):
        matches = self.retrieve("vector")

        self.assertEqual(
            matches[0]["document_id"],
            "DOC001"
        )

        self.reranker.assert_not_called()

    def test_reranked_strategy(self):
        matches = self.retrieve("reranked")

        self.assertEqual(
            matches[0]["document_id"],
            "DOC002"
        )

        self.reranker.assert_called_once()

    def test_full_strategy(self):
        matches = self.retrieve("full")

        self.assertEqual(
            matches[0]["document_id"],
            "DOC003"
        )

        self.reranker.assert_called_once()

    def test_unique_pages(self):
        matches = self.retrieve("vector")

        pages = [
            (match["document_id"], match["page_number"])
            for match in matches
        ]

        self.assertEqual(len(pages), 3)
        self.assertEqual(len(pages), len(set(pages)))

    def test_respects_top_k(self):
        matches = self.retrieve("vector", k=2)

        self.assertEqual(len(matches), 2)

    def test_same_candidate_pool(self):
        for strategy in ["vector", "reranked", "full"]:
            self.retrieve(strategy)

        candidate_counts = [
            call.kwargs["n_results"]
            for call in self.collection.query.call_args_list
        ]

        self.assertEqual(candidate_counts, [20, 20, 20])

    def test_invalid_strategy(self):
        with self.assertRaises(ValueError):
            create_retriever(
                self.collection,
                self.model,
                strategy="invalid"
            )

    def test_empty_collection(self):
        self.collection.count.return_value = 0

        matches = self.retrieve("full")

        self.assertEqual(matches, [])
        self.reranker.assert_not_called()


if __name__ == "__main__":
    unittest.main()
