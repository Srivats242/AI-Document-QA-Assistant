import unittest
from unittest.mock import Mock

from evaluation.runner import (
    normalize_matches,
    evaluate_question,
    summarize_results,
    summarize_by_group,
    run_evaluation
)


class TestEvaluationRunner(unittest.TestCase):

    def setUp(self):
        self.question = {
            "question_id": "Q001",
            "question": "What is the main purpose?",
            "category": "technical",
            "question_type": "factual",
            "difficulty": "easy",
            "expected_answer": "Example answer",
            "relevant_sources": [
                {
                    "document_id": "DOC001",
                    "page_number": 3
                }
            ],
            "split": "development"
        }

        self.document_id_map = {
            "runtime-001": "DOC001",
            "runtime-002": "DOC002"
        }

        self.matches = [
            {
                "document_id": "runtime-001",
                "page_number": 3
            },
            {
                "document_id": "runtime-002",
                "page_number": 5
            }
        ]

    def test_normalize_matches(self):
        result = normalize_matches(
            self.matches,
            self.document_id_map
        )

        self.assertEqual(
            result,
            ["DOC001:page:3", "DOC002:page:5"]
        )

    def test_normalize_duplicate_pages(self):
        matches = [
            self.matches[0],
            self.matches[0],
            self.matches[1]
        ]

        result = normalize_matches(
            matches,
            self.document_id_map
        )

        self.assertEqual(len(result), 2)

    def test_unknown_document_id(self):
        matches = [
            {
                "document_id": "unknown",
                "page_number": 1
            }
        ]

        with self.assertRaises(ValueError):
            normalize_matches(
                matches,
                self.document_id_map
            )

    def test_evaluate_question(self):
        retrieve_fn = Mock(return_value=self.matches)

        result = evaluate_question(
            self.question,
            retrieve_fn,
            self.document_id_map,
            k=2
        )

        self.assertEqual(result["question_id"], "Q001")
        self.assertEqual(
            result["metrics"]["precision@2"], 0.5
        )
        self.assertEqual(
            result["metrics"]["recall@2"], 1.0
        )
        self.assertEqual(
            result["metrics"]["hit_rate@2"], 1.0
        )
        self.assertGreaterEqual(result["latency_ms"], 0)

        retrieve_fn.assert_called_once_with(
            self.question["question"], 2
        )

    def test_evaluate_no_matches(self):
        result = evaluate_question(
            self.question,
            Mock(return_value=[]),
            self.document_id_map,
            k=5
        )

        self.assertEqual(
            result["metrics"]["precision@5"], 0.0
        )
        self.assertEqual(
            result["metrics"]["recall@5"], 0.0
        )
        self.assertEqual(
            result["metrics"]["hit_rate@5"], 0.0
        )

    def test_evaluate_irrelevant_matches(self):
        result = evaluate_question(
            self.question,
            Mock(return_value=[self.matches[1]]),
            self.document_id_map,
            k=1
        )

        self.assertEqual(
            result["metrics"]["recall@1"], 0.0
        )
        self.assertEqual(
            result["metrics"]["ndcg@1"], 0.0
        )

    def test_invalid_k(self):
        with self.assertRaises(ValueError):
            evaluate_question(
                self.question,
                Mock(),
                self.document_id_map,
                k=0
            )

    def test_summarize_results(self):
        results = [
            {
                "latency_ms": 10,
                "metrics": {"recall@5": 1.0}
            },
            {
                "latency_ms": 20,
                "metrics": {"recall@5": 0.0}
            }
        ]

        summary = summarize_results(results)

        self.assertEqual(summary["total_questions"], 2)
        self.assertEqual(summary["average_latency_ms"], 15)
        self.assertEqual(
            summary["metrics"]["recall@5"], 0.5
        )

    def test_summarize_empty_results(self):
        summary = summarize_results([])

        self.assertEqual(summary["total_questions"], 0)
        self.assertEqual(summary["metrics"], {})

    def test_summarize_by_category(self):
        results = [
            {
                "category": "technical",
                "latency_ms": 10,
                "metrics": {"recall@5": 1.0}
            },
            {
                "category": "academic",
                "latency_ms": 20,
                "metrics": {"recall@5": 0.0}
            }
        ]

        summary = summarize_by_group(
            results, "category"
        )

        self.assertEqual(
            summary["technical"]["metrics"]["recall@5"],
            1.0
        )
        self.assertEqual(
            summary["academic"]["metrics"]["recall@5"],
            0.0
        )

    def test_run_evaluation(self):
        second_question = {
            **self.question,
            "question_id": "Q002",
            "question": "What is the second topic?",
            "difficulty": "medium"
        }

        retrieve_fn = Mock(return_value=self.matches)

        report = run_evaluation(
            [self.question, second_question],
            retrieve_fn,
            self.document_id_map,
            k=2
        )

        self.assertEqual(
            report["summary"]["total_questions"], 2
        )
        self.assertEqual(len(report["results"]), 2)
        self.assertEqual(retrieve_fn.call_count, 2)
        self.assertIn("technical", report["by_category"])
        self.assertIn("easy", report["by_difficulty"])
        self.assertIn("medium", report["by_difficulty"])
        self.assertIn("factual", report["by_question_type"])
        self.assertIn("development", report["by_split"])

    def test_run_evaluation_empty_dataset(self):
        retrieve_fn = Mock()

        report = run_evaluation(
            [],
            retrieve_fn,
            self.document_id_map
        )

        self.assertEqual(
            report["summary"]["total_questions"], 0
        )

        retrieve_fn.assert_not_called()

    def test_run_evaluation_invalid_dataset(self):
        with self.assertRaises(ValueError):
            run_evaluation(
                [self.question, self.question],
                Mock(),
                self.document_id_map
            )


if __name__ == "__main__":
    unittest.main()
