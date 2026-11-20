import unittest

from rag_prompt import build_rag_prompt


class TestRAGPrompt(unittest.TestCase):

    def setUp(self):
        self.matches = [
            {
                "filename": "Kim.pdf",
                "page_number": 18,
                "text": "Korean missionaries supported development in Cambodia."
            },
            {
                "filename": "Kim.pdf",
                "page_number": 16,
                "text": "The church promoted Koreanized Pentecostalism."
            }
        ]

    def test_includes_question(self):
        prompt = build_rag_prompt(
            "What role did Korean missionaries play?",
            self.matches
        )

        self.assertIn(
            "What role did Korean missionaries play?",
            prompt
        )

    def test_includes_source_metadata(self):
        prompt = build_rag_prompt(
            "Test question",
            self.matches
        )

        self.assertIn("[1] Document: Kim.pdf", prompt)
        self.assertIn("Page: 18", prompt)
        self.assertIn("[2] Document: Kim.pdf", prompt)
        self.assertIn("Page: 16", prompt)

    def test_includes_grounding_rules(self):
        prompt = build_rag_prompt(
            "Test question",
            self.matches
        )

        self.assertIn(
            "Every factual claim must be directly supported",
            prompt
        )

        self.assertIn(
            "Do not combine passages to create conclusions",
            prompt
        )

        self.assertIn(
            "Never transfer activities, achievements",
            prompt
        )

        self.assertIn(
            "Preserve who performed an action",
            prompt
        )


    def test_includes_citation_rules(self):
        prompt = build_rag_prompt(
            "Test question",
            self.matches
        )

        self.assertIn(
            "Place citations immediately after",
            prompt
        )

        self.assertIn(
            "Do not invent citation numbers",
            prompt
        )

    def test_rejects_empty_question(self):
        with self.assertRaises(ValueError):
            build_rag_prompt("   ", self.matches)

    def test_rejects_empty_matches(self):
        with self.assertRaises(ValueError):
            build_rag_prompt("Test question", [])


if __name__ == "__main__":
    unittest.main()
