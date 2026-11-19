import unittest

from text_cleaner import clean_extracted_text


class TestTextCleaner(unittest.TestCase):

    def test_removes_line_break_hyphenation(self):
        text = "Korean missionaries helped Cambo-\ndians."
        expected = "Korean missionaries helped Cambodians."

        self.assertEqual(clean_extracted_text(text), expected)

    def test_preserves_normal_hyphenated_words(self):
        text = "They organized short-term missions."

        self.assertEqual(clean_extracted_text(text), text)

    def test_removes_soft_hyphens(self):
        text = "bene\u00adficial actions"
        expected = "beneficial actions"

        self.assertEqual(clean_extracted_text(text), expected)

    def test_normalizes_whitespace(self):
        text = "Korean   missionaries\n\n\nhelped communities."
        expected = "Korean missionaries\n\nhelped communities."

        self.assertEqual(clean_extracted_text(text), expected)

    def test_handles_empty_text(self):
        self.assertEqual(clean_extracted_text(""), "")


if __name__ == "__main__":
    unittest.main()
