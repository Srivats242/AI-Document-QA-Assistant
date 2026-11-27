from collections import defaultdict
from statistics import mean
from time import perf_counter

from evaluation.dataset import (
    validate_dataset,
    get_relevant_source_keys,
    source_key
)
from evaluation.metrics import evaluate_retrieval


def normalize_matches(matches, document_id_map):
    retrieved = []

    for match in matches:
        runtime_id = match["document_id"]

        if runtime_id not in document_id_map:
            raise ValueError(
                f"Unmapped document ID: {runtime_id}"
            )

        benchmark_id = document_id_map[runtime_id]

        retrieved.append(
            source_key(benchmark_id, match["page_number"])
        )

    return list(dict.fromkeys(retrieved))


def evaluate_question(
    question,
    retrieve_fn,
    document_id_map,
    k=5
):
    if k <= 0:
        raise ValueError("k must be greater than zero")

    start = perf_counter()
    matches = retrieve_fn(question["question"], k)
    latency_ms = (perf_counter() - start) * 1000

    retrieved = normalize_matches(
        matches,
        document_id_map
    )[:k]

    relevant = get_relevant_source_keys(question)

    metrics = evaluate_retrieval(
        retrieved,
        relevant,
        k
    )

    return {
        "question_id": question["question_id"],
        "question": question["question"],
        "category": question["category"],
        "question_type": question["question_type"],
        "difficulty": question["difficulty"],
        "split": question["split"],
        "retrieved_sources": retrieved,
        "relevant_sources": sorted(relevant),
        "latency_ms": latency_ms,
        "metrics": metrics
    }


def summarize_results(results):
    if not results:
        return {
            "total_questions": 0,
            "average_latency_ms": 0.0,
            "metrics": {}
        }

    metric_names = results[0]["metrics"].keys()

    return {
        "total_questions": len(results),
        "average_latency_ms": mean(
            result["latency_ms"] for result in results
        ),
        "metrics": {
            name: mean(
                result["metrics"][name]
                for result in results
            )
            for name in metric_names
        }
    }


def summarize_by_group(results, field):
    groups = defaultdict(list)

    for result in results:
        groups[result[field]].append(result)

    return {
        name: summarize_results(group)
        for name, group in sorted(groups.items())
    }


def run_evaluation(
    questions,
    retrieve_fn,
    document_id_map,
    k=5
):
    validate_dataset(questions)

    if k <= 0:
        raise ValueError("k must be greater than zero")

    results = []

    for question in questions:
        result = evaluate_question(
            question,
            retrieve_fn,
            document_id_map,
            k
        )

        results.append(result)

    return {
        "k": k,
        "summary": summarize_results(results),
        "by_category": summarize_by_group(
            results, "category"
        ),
        "by_difficulty": summarize_by_group(
            results, "difficulty"
        ),
        "by_question_type": summarize_by_group(
            results, "question_type"
        ),
        "by_split": summarize_by_group(
            results, "split"
        ),
        "results": results
    }
