import unittest

from rag_prompt import build_rag_prompt


class TestRAGPrompt(unittest.TestCase):

    def setUp(self):
        self.matches = [
            {
                "filename": "Kim.pdf",
                "page_number": 4,
                "text": "Missionaries established schools and community programs.",
                "distance": 0.25,
            },
            {
                "filename": "Sarfati.pdf",
                "page_number": 7,
                "text": "Religious organizations contributed to local development.",
                "distance": 0.32,
            },
        ]

    def test_prompt_contains_question(self):
        prompt = build_rag_prompt(
            "What role do missionaries play?",
            self.matches,
        )

        self.assertIn("What role do missionaries play?", prompt)

    def test_prompt_contains_sources(self):
        prompt = build_rag_prompt("Explain the documents.", self.matches)

        self.assertIn("Kim.pdf", prompt)
        self.assertIn("Sarfati.pdf", prompt)
        self.assertIn("Page: 4", prompt)
        self.assertIn("Page: 7", prompt)

    def test_prompt_contains_citation_markers(self):
        prompt = build_rag_prompt("Explain the documents.", self.matches)

        self.assertIn("[1] Document:", prompt)
        self.assertIn("[2] Document:", prompt)

    def test_empty_question_raises_error(self):
        with self.assertRaises(ValueError):
            build_rag_prompt("", self.matches)

    def test_empty_matches_raises_error(self):
        with self.assertRaises(ValueError):
            build_rag_prompt("What happened?", [])


if __name__ == "__main__":
    unittest.main()
