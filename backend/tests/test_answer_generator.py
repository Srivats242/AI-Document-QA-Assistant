import unittest
from unittest.mock import MagicMock

from answer_generator import generate_answer


class TestAnswerGenerator(unittest.TestCase):

    def setUp(self):
        self.matches = [
            {
                "filename": "Kim.pdf",
                "page_number": 4,
                "text": "Missionaries established schools.",
            }
        ]

        self.client = MagicMock()
        self.client.responses.create.return_value.output_text = (
            "Missionaries established schools [1]."
        )

    def test_generates_answer(self):
        answer = generate_answer(
            "What did missionaries establish?",
            self.matches,
            client=self.client,
            model="test-model",
        )

        self.assertEqual(
            answer,
            "Missionaries established schools [1].",
        )

    def test_calls_model_with_document_context(self):
        generate_answer(
            "What did missionaries establish?",
            self.matches,
            client=self.client,
            model="test-model",
        )

        arguments = self.client.responses.create.call_args.kwargs

        self.assertEqual(arguments["model"], "test-model")
        self.assertIn("Kim.pdf", arguments["input"])
        self.assertIn("Page: 4", arguments["input"])
        self.assertFalse(arguments["store"])

    def test_empty_question_raises_error(self):
        with self.assertRaises(ValueError):
            generate_answer(
                "",
                self.matches,
                client=self.client,
            )

        self.client.responses.create.assert_not_called()

    def test_empty_model_response_raises_error(self):
        self.client.responses.create.return_value.output_text = " "

        with self.assertRaises(ValueError):
            generate_answer(
                "What did missionaries establish?",
                self.matches,
                client=self.client,
            )


if __name__ == "__main__":
    unittest.main()
