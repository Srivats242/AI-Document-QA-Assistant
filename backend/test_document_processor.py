import unittest

from document_processor import clean_text, chunk_document


class TestDocumentProcessor(unittest.TestCase):

    def test_clean_text(self):
        text = "Hello   world!\nThis is a test."
        self.assertEqual(
            clean_text(text),
            "Hello world! This is a test."
        )

    def test_empty_document(self):
        self.assertEqual(chunk_document([]), [])

    def test_short_document(self):
        pages = [
            {"page_number": 1, "text": "This is a short document."}
        ]

        chunks = chunk_document(pages)

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]["page_number"], 1)
        self.assertEqual(chunks[0]["text"], "This is a short document.")

    def test_long_document(self):
        pages = [
            {"page_number": 1, "text": "Artificial intelligence " * 100}
        ]

        chunks = chunk_document(pages, chunk_size=100, overlap=20)

        self.assertGreater(len(chunks), 1)

        for chunk in chunks:
            self.assertLessEqual(len(chunk["text"]), 100)

    def test_invalid_chunk_size(self):
        with self.assertRaises(ValueError):
            chunk_document([], chunk_size=0)

    def test_invalid_overlap(self):
        with self.assertRaises(ValueError):
            chunk_document([], chunk_size=100, overlap=100)


if __name__ == "__main__":
    unittest.main()
