import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from evaluation.dataset import (
    source_key,
    validate_question,
    validate_dataset,
    load_dataset,
    get_relevant_source_keys,
    filter_by_split,
    dataset_summary
)


class TestDataset(unittest.TestCase):

    def setUp(self):
        self.question = {
            "question_id": "Q001",
            "question": "What is the purpose of the method?",
            "category": "academic",
            "question_type": "factual",
            "difficulty": "easy",
            "expected_answer": "Sample test answer.",
            "relevant_sources": [
                {
                    "document_id": "DOC001",
                    "page_number": 3
                }
            ],
            "split": "development"
        }

    def test_valid_question(self):
        validate_question(self.question)

    def test_missing_required_field(self):
        del self.question["expected_answer"]

        with self.assertRaises(ValueError):
            validate_question(self.question)

    def test_empty_question(self):
        self.question["question"] = ""

        with self.assertRaises(ValueError):
            validate_question(self.question)

    def test_invalid_category(self):
        self.question["category"] = "invalid"

        with self.assertRaises(ValueError):
            validate_question(self.question)

    def test_invalid_question_type(self):
        self.question["question_type"] = "invalid"

        with self.assertRaises(ValueError):
            validate_question(self.question)

    def test_invalid_difficulty(self):
        self.question["difficulty"] = "invalid"

        with self.assertRaises(ValueError):
            validate_question(self.question)

    def test_invalid_split(self):
        self.question["split"] = "invalid"

        with self.assertRaises(ValueError):
            validate_question(self.question)

    def test_empty_relevant_sources(self):
        self.question["relevant_sources"] = []

        with self.assertRaises(ValueError):
            validate_question(self.question)

    def test_invalid_page_number(self):
        for page_number in [0, -1, True, "3"]:
            with self.subTest(page_number=page_number):
                with self.assertRaises(ValueError):
                    source_key("DOC001", page_number)

    def test_duplicate_sources(self):
        self.question["relevant_sources"].append(
            {"document_id": "DOC001", "page_number": 3}
        )

        with self.assertRaises(ValueError):
            validate_question(self.question)

    def test_duplicate_question_ids(self):
        second_question = {
            **self.question,
            "question": "What are the main findings?"
        }

        with self.assertRaisesRegex(
            ValueError, "Duplicate question ID"
        ):
            validate_dataset([self.question, second_question])

    def test_document_leakage(self):
        second_question = {
            **self.question,
            "question_id": "Q002",
            "question": "What are the main findings?",
            "split": "test"
        }

        with self.assertRaisesRegex(
            ValueError, "Document leakage detected"
        ):
            validate_dataset([self.question, second_question])

    def test_relevant_source_keys(self):
        self.assertEqual(
            get_relevant_source_keys(self.question),
            {"DOC001:page:3"}
        )

    def test_dataset_summary_and_split(self):
        questions = [self.question]
        summary = dataset_summary(questions)

        self.assertEqual(summary["total_questions"], 1)
        self.assertEqual(summary["total_documents"], 1)
        self.assertEqual(summary["categories"], {"academic": 1})
        self.assertEqual(summary["splits"], {"development": 1})

        self.assertEqual(
            filter_by_split(questions, "development"),
            questions
        )

        self.assertEqual(
            filter_by_split(questions, "test"),
            []
        )

    def test_load_dataset(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "benchmark.json"

            path.write_text(
                json.dumps([self.question]),
                encoding="utf-8"
            )

            self.assertEqual(
                load_dataset(path),
                [self.question]
            )


if __name__ == "__main__":
    unittest.main()
