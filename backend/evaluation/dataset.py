import json
from pathlib import Path


VALID_CATEGORIES = {
    "academic",
    "technical",
    "government",
    "financial",
    "educational",
    "scanned"
}

VALID_QUESTION_TYPES = {
    "factual",
    "conceptual",
    "comparison",
    "multi_hop",
    "numerical"
}

VALID_DIFFICULTIES = {
    "easy",
    "medium",
    "hard"
}

VALID_SPLITS = {
    "development",
    "test"
}


def _require_text(value, field: str) -> None:
    """Validate a required non-empty text field."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")


def source_key(document_id: str, page_number: int) -> str:
    """Create a stable identifier for a document page."""
    _require_text(document_id, "document_id")

    if type(page_number) is not int or page_number < 1:
        raise ValueError("page_number must be a positive integer")

    return f"{document_id}:page:{page_number}"


def validate_question(question: dict) -> None:
    """Validate an individual benchmark question."""
    if not isinstance(question, dict):
        raise ValueError("Each question must be an object")

    for field in [
        "question_id",
        "question",
        "expected_answer"
    ]:
        _require_text(question.get(field), field)

    allowed_fields = {
        "category": VALID_CATEGORIES,
        "question_type": VALID_QUESTION_TYPES,
        "difficulty": VALID_DIFFICULTIES,
        "split": VALID_SPLITS
    }

    for field, allowed_values in allowed_fields.items():
        value = question.get(field)

        if not isinstance(value, str) or value not in allowed_values:
            raise ValueError(f"Invalid {field}: {value}")

    sources = question.get("relevant_sources")

    if not isinstance(sources, list) or not sources:
        raise ValueError(
            "Each question must have at least one relevant source"
        )

    seen_sources = set()

    for source in sources:
        if not isinstance(source, dict):
            raise ValueError("Each source must be an object")

        key = source_key(
            source.get("document_id"),
            source.get("page_number")
        )

        if key in seen_sources:
            raise ValueError(f"Duplicate relevant source: {key}")

        seen_sources.add(key)


def validate_dataset(questions: list[dict]) -> None:
    """Validate benchmark records and detect dataset leakage."""
    if not isinstance(questions, list):
        raise ValueError("Benchmark dataset must be a list")

    seen_ids = set()
    seen_questions = set()
    document_splits = {}

    for question in questions:
        validate_question(question)

        question_id = question["question_id"]

        if question_id in seen_ids:
            raise ValueError(
                f"Duplicate question ID: {question_id}"
            )

        seen_ids.add(question_id)

        normalized_question = " ".join(
            question["question"].lower().split()
        )

        if normalized_question in seen_questions:
            raise ValueError(
                f"Duplicate question text: {question_id}"
            )

        seen_questions.add(normalized_question)

        split = question["split"]

        for source in question["relevant_sources"]:
            document_id = source["document_id"]

            if document_id in document_splits:
                if document_splits[document_id] != split:
                    raise ValueError(
                        f"Document leakage detected: {document_id}"
                    )

            document_splits[document_id] = split


def load_dataset(path: str | Path) -> list[dict]:
    """Load and validate a JSON benchmark dataset."""
    path = Path(path)

    with path.open("r", encoding="utf-8-sig") as file:
        questions = json.load(file)

    validate_dataset(questions)

    return questions


def get_relevant_source_keys(question: dict) -> set[str]:
    """Convert ground-truth sources into retrieval metric IDs."""
    validate_question(question)

    return {
        source_key(
            source["document_id"],
            source["page_number"]
        )
        for source in question["relevant_sources"]
    }


def filter_by_split(
    questions: list[dict],
    split: str
) -> list[dict]:
    """Return questions belonging to a particular dataset split."""
    if split not in VALID_SPLITS:
        raise ValueError(f"Invalid split: {split}")

    return [
        question
        for question in questions
        if question["split"] == split
    ]


def dataset_summary(questions: list[dict]) -> dict:
    """Calculate basic benchmark dataset statistics."""
    validate_dataset(questions)

    summary = {
        "total_questions": len(questions),
        "total_documents": 0,
        "categories": {},
        "question_types": {},
        "difficulties": {},
        "splits": {}
    }

    documents = set()

    for question in questions:
        fields = {
            "categories": question["category"],
            "question_types": question["question_type"],
            "difficulties": question["difficulty"],
            "splits": question["split"]
        }

        for group, value in fields.items():
            counts = summary[group]
            counts[value] = counts.get(value, 0) + 1

        for source in question["relevant_sources"]:
            documents.add(source["document_id"])

    summary["total_documents"] = len(documents)

    return summary
