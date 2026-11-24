import math
import unittest

from evaluation.metrics import (
    precision_at_k,
    recall_at_k,
    hit_rate_at_k,
    reciprocal_rank,
    mean_reciprocal_rank,
    ndcg_at_k,
    evaluate_retrieval
)


class TestPrecision(unittest.TestCase):

    def test_perfect_precision(self):
        self.assertEqual(
            precision_at_k(["A", "B", "C"], {"A", "B", "C"}, 3),
            1.0
        )

    def test_partial_precision(self):
        self.assertAlmostEqual(
            precision_at_k(
                ["A", "B", "C", "D", "E"], {"B", "D", "F"}, 5
            ),
            0.4
        )

    def test_no_relevant_results(self):
        self.assertEqual(
            precision_at_k(["A", "B"], {"C"}, 2),
            0.0
        )

    def test_fewer_results_than_k(self):
        self.assertAlmostEqual(
            precision_at_k(["A", "B"], {"A", "B"}, 5),
            0.4
        )

    def test_duplicate_results(self):
        self.assertAlmostEqual(
            precision_at_k(["A", "A", "B"], {"A", "B"}, 3),
            2 / 3
        )


class TestRecall(unittest.TestCase):

    def test_perfect_recall(self):
        self.assertEqual(
            recall_at_k(["A", "B", "C"], {"A", "B"}, 3),
            1.0
        )

    def test_partial_recall(self):
        self.assertAlmostEqual(
            recall_at_k(
                ["A", "B", "C", "D", "E"], {"B", "D", "F"}, 5
            ),
            2 / 3
        )

    def test_empty_relevant_set(self):
        self.assertEqual(
            recall_at_k(["A", "B"], set(), 2),
            0.0
        )

    def test_empty_retrieval(self):
        self.assertEqual(
            recall_at_k([], {"A", "B"}, 5),
            0.0
        )

    def test_retrieval_cutoff(self):
        self.assertEqual(
            recall_at_k(["A", "B", "C"], {"C"}, 2),
            0.0
        )


class TestHitRate(unittest.TestCase):

    def test_successful_hit(self):
        self.assertEqual(
            hit_rate_at_k(["A", "B"], {"B"}, 2),
            1.0
        )

    def test_unsuccessful_hit(self):
        self.assertEqual(
            hit_rate_at_k(["A", "B"], {"C"}, 2),
            0.0
        )

    def test_hit_outside_cutoff(self):
        self.assertEqual(
            hit_rate_at_k(["A", "B", "C"], {"C"}, 2),
            0.0
        )


class TestReciprocalRank(unittest.TestCase):

    def test_first_result_relevant(self):
        self.assertEqual(
            reciprocal_rank(["A", "B", "C"], {"A"}),
            1.0
        )

    def test_second_result_relevant(self):
        self.assertEqual(
            reciprocal_rank(["A", "B", "C"], {"B"}),
            0.5
        )

    def test_no_relevant_result(self):
        self.assertEqual(
            reciprocal_rank(["A", "B"], {"C"}),
            0.0
        )

    def test_mean_reciprocal_rank(self):
        rankings = [
            ["A", "B", "C"],
            ["D", "E", "F"]
        ]

        relevant_sets = [{"B"}, {"D"}]

        self.assertAlmostEqual(
            mean_reciprocal_rank(rankings, relevant_sets),
            0.75
        )

    def test_empty_rankings(self):
        self.assertEqual(
            mean_reciprocal_rank([], []),
            0.0
        )

    def test_mismatched_input_lengths(self):
        with self.assertRaises(ValueError):
            mean_reciprocal_rank(
                [["A"], ["B"]], [{"A"}]
            )


class TestNDCG(unittest.TestCase):

    def test_perfect_ranking(self):
        self.assertAlmostEqual(
            ndcg_at_k(["A", "B", "C"], {"A", "B"}, 3),
            1.0
        )

    def test_imperfect_ranking(self):
        retrieved = ["A", "B", "C", "D", "E"]
        relevant = {"B", "D", "F"}

        dcg = 1 / math.log2(3) + 1 / math.log2(5)
        ideal_dcg = 1 + 1 / math.log2(3) + 1 / math.log2(4)

        self.assertAlmostEqual(
            ndcg_at_k(retrieved, relevant, 5),
            dcg / ideal_dcg
        )

    def test_no_relevant_results(self):
        self.assertEqual(
            ndcg_at_k(["A", "B"], {"C"}, 2),
            0.0
        )

    def test_empty_relevant_set(self):
        self.assertEqual(
            ndcg_at_k(["A", "B"], set(), 2),
            0.0
        )


class TestEvaluation(unittest.TestCase):

    def test_combined_metrics(self):
        results = evaluate_retrieval(
            ["A", "B", "C", "D", "E"],
            {"B", "D", "F"},
            5
        )

        self.assertEqual(len(results), 5)
        self.assertAlmostEqual(results["precision@5"], 0.4)
        self.assertAlmostEqual(results["recall@5"], 2 / 3)
        self.assertEqual(results["hit_rate@5"], 1.0)
        self.assertEqual(results["reciprocal_rank@5"], 0.5)

        expected_ndcg = (
            (1 / math.log2(3) + 1 / math.log2(5))
            / (1 + 1 / math.log2(3) + 1 / math.log2(4))
        )

        self.assertAlmostEqual(
            results["ndcg@5"],
            expected_ndcg
        )

    def test_invalid_cutoff(self):
        functions = [
            precision_at_k,
            recall_at_k,
            hit_rate_at_k,
            ndcg_at_k,
            evaluate_retrieval
        ]

        for function in functions:
            for k in [0, -1]:
                with self.subTest(function=function.__name__, k=k):
                    with self.assertRaises(ValueError):
                        function(["A"], {"A"}, k)


if __name__ == "__main__":
    unittest.main()
