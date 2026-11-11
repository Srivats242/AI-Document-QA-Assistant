import unittest

from document_processor import clean_text, chunk_document


class TestDocumentProcessor(unittest.TestCase):

    def test_clean_text(self):
        text = "Hello   world!\nThis is a test."
        self.assertEqual(
            clean_text(text),
            "Hello world! This is a test."
        )

    
    def test_clean_text_control_characters(self):
        text = "Hello\x00world\x07! Testing."

        self.assertEqual(
            clean_text(text),
            "Hello world ! Testing."
        )

    def test_clean_text_ligatures(self):
        text = "The ﬁnal ﬂight was diﬃcult."

        self.assertEqual(
            clean_text(text),
            "The final flight was difficult."
        )

    def test_clean_text_invisible_characters(self):
        text = "This is a docu\u200bment with co\u00adoperation."

        self.assertEqual(
            clean_text(text),
            "This is a document with cooperation."
        )

    def test_clean_text_unicode(self):
        text = "Cafe\u0301 and résumé"

        self.assertEqual(
            clean_text(text),
            "Café and résumé"
        )

    def test_clean_text_whitespace(self):
        text = "  Hello\t\tworld!\n\nThis is a test.  "

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
