import math

import pytest

from evaluation.metrics import (
    precision_at_k,
    recall_at_k,
    hit_rate_at_k,
    reciprocal_rank,
    mean_reciprocal_rank,
    ndcg_at_k,
    evaluate_retrieval
)


class TestPrecision:

    def test_perfect_precision(self):
        assert precision_at_k(
            ["A", "B", "C"], {"A", "B", "C"}, 3
        ) == 1.0

    def test_partial_precision(self):
        assert precision_at_k(
            ["A", "B", "C", "D", "E"], {"B", "D", "F"}, 5
        ) == pytest.approx(0.4)

    def test_no_relevant_results(self):
        assert precision_at_k(
            ["A", "B"], {"C"}, 2
        ) == 0.0

    def test_fewer_results_than_k(self):
        assert precision_at_k(
            ["A", "B"], {"A", "B"}, 5
        ) == pytest.approx(0.4)

    def test_duplicate_results(self):
        assert precision_at_k(
            ["A", "A", "B"], {"A", "B"}, 3
        ) == pytest.approx(2 / 3)


class TestRecall:

    def test_perfect_recall(self):
        assert recall_at_k(
            ["A", "B", "C"], {"A", "B"}, 3
        ) == 1.0

    def test_partial_recall(self):
        assert recall_at_k(
            ["A", "B", "C", "D", "E"], {"B", "D", "F"}, 5
        ) == pytest.approx(2 / 3)

    def test_empty_relevant_set(self):
        assert recall_at_k(
            ["A", "B"], set(), 2
        ) == 0.0

    def test_empty_retrieval(self):
        assert recall_at_k(
            [], {"A", "B"}, 5
        ) == 0.0

    def test_retrieval_cutoff(self):
        assert recall_at_k(
            ["A", "B", "C"], {"C"}, 2
        ) == 0.0


class TestHitRate:

    def test_successful_hit(self):
        assert hit_rate_at_k(
            ["A", "B"], {"B"}, 2
        ) == 1.0

    def test_unsuccessful_hit(self):
        assert hit_rate_at_k(
            ["A", "B"], {"C"}, 2
        ) == 0.0

    def test_hit_outside_cutoff(self):
        assert hit_rate_at_k(
            ["A", "B", "C"], {"C"}, 2
        ) == 0.0


class TestReciprocalRank:

    def test_first_result_relevant(self):
        assert reciprocal_rank(
            ["A", "B", "C"], {"A"}
        ) == 1.0

    def test_second_result_relevant(self):
        assert reciprocal_rank(
            ["A", "B", "C"], {"B"}
        ) == 0.5

    def test_no_relevant_result(self):
        assert reciprocal_rank(
            ["A", "B"], {"C"}
        ) == 0.0

    def test_mean_reciprocal_rank(self):
        rankings = [
            ["A", "B", "C"],
            ["D", "E", "F"]
        ]

        relevant_sets = [{"B"}, {"D"}]

        assert mean_reciprocal_rank(
            rankings, relevant_sets
        ) == pytest.approx(0.75)

    def test_empty_rankings(self):
        assert mean_reciprocal_rank([], []) == 0.0

    def test_mismatched_input_lengths(self):
        with pytest.raises(ValueError):
            mean_reciprocal_rank(
                [["A"], ["B"]], [{"A"}]
            )


class TestNDCG:

    def test_perfect_ranking(self):
        assert ndcg_at_k(
            ["A", "B", "C"], {"A", "B"}, 3
        ) == pytest.approx(1.0)

    def test_imperfect_ranking(self):
        retrieved = ["A", "B", "C", "D", "E"]
        relevant = {"B", "D", "F"}

        dcg = 1 / math.log2(3) + 1 / math.log2(5)
        ideal_dcg = 1 + 1 / math.log2(3) + 1 / math.log2(4)

        assert ndcg_at_k(
            retrieved, relevant, 5
        ) == pytest.approx(dcg / ideal_dcg)

    def test_no_relevant_results(self):
        assert ndcg_at_k(
            ["A", "B"], {"C"}, 2
        ) == 0.0

    def test_empty_relevant_set(self):
        assert ndcg_at_k(
            ["A", "B"], set(), 2
        ) == 0.0


class TestEvaluation:

    def test_combined_metrics(self):
        results = evaluate_retrieval(
            ["A", "B", "C", "D", "E"],
            {"B", "D", "F"},
            5
        )

        assert len(results) == 5
        assert results["precision@5"] == pytest.approx(0.4)
        assert results["recall@5"] == pytest.approx(2 / 3)
        assert results["hit_rate@5"] == 1.0
        assert results["reciprocal_rank@5"] == 0.5

        expected_ndcg = (
            (1 / math.log2(3) + 1 / math.log2(5))
            / (1 + 1 / math.log2(3) + 1 / math.log2(4))
        )

        assert results["ndcg@5"] == pytest.approx(expected_ndcg)

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
                with pytest.raises(ValueError):
                    function(["A"], {"A"}, k)
