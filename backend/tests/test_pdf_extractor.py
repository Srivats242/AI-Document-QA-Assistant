import unittest
from unittest.mock import MagicMock, patch

from pdf_extractor import needs_ocr, extract_page_text


class TestPDFExtractor(unittest.TestCase):

    def test_detects_corrupted_text(self):
        self.assertTrue(needs_ocr("A signi,-cant improvement"))
        self.assertTrue(needs_ocr("Cha$t&r 8"))
        self.assertTrue(needs_ocr(""))

    def test_accepts_normal_text(self):
        self.assertFalse(
            needs_ocr("Korean missionaries worked in Cambodia.")
        )

    def test_normal_extraction(self):
        page = MagicMock()
        page.get_text.return_value = "Normal PDF text."

        result = extract_page_text(page)

        self.assertEqual(result, "Normal PDF text.")
        page.get_textpage_ocr.assert_not_called()

    @patch("pdf_extractor.Path.is_dir", return_value=True)
    def test_ocr_fallback(self, mock_is_dir):
        page = MagicMock()

        page.get_text.side_effect = [
            "This is signi,-cant.",
            "This is significant.",
        ]

        result = extract_page_text(page)

        self.assertEqual(result, "This is significant.")
        page.get_textpage_ocr.assert_called_once()


if __name__ == "__main__":
    unittest.main()
