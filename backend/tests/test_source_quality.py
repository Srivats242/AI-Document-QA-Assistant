import unittest

from source_quality import (
    is_bibliography_heavy,
    rerank_for_source_quality,
)


class TestSourceQuality(unittest.TestCase):

    def test_detects_bibliography(self):
        text = """
        Hughes, Caroline. Cambodia's Economic
        Transformation. NIAS Press, 2011.

        Iwabuchi, Koichi. Asian Modernities.
        Hong Kong University Press, 2004.

        Jang, Suk-man. Protestantism in Korea.
        Korea Journal, 1999.
        """

        self.assertTrue(is_bibliography_heavy(text))

    def test_accepts_normal_academic_text(self):
        text = """
        Korean missionaries contributed to
        development in Cambodia through religious
        networks and economic cooperation.
        """

        self.assertFalse(is_bibliography_heavy(text))

    def test_accepts_historical_dates(self):
        text = """
        South Korea experienced major changes
        in 1950, 1980, and 2000. These changes
        influenced its religious development.
        """

        self.assertFalse(is_bibliography_heavy(text))

    def test_accepts_empty_text(self):
        self.assertFalse(is_bibliography_heavy(""))
        self.assertFalse(is_bibliography_heavy("   "))


    def test_penalizes_bibliography_passages(self):
        bibliography = (
            "Smith. Academic Press, 1999. "
            "Jones. Research Journal, 2004. "
            "Brown. University Press, 2015."
        )

        matches = [
            {
                "text": bibliography,
                "relevance_score": 4.2
            },
            {
                "text": "Korean missionaries supported development.",
                "relevance_score": 3.5
            }
        ]

        results = rerank_for_source_quality(
            "How did missionaries support development?",
            matches
        )

        self.assertEqual(
            results[0]["text"],
            "Korean missionaries supported development."
        )

        # Original scores should remain unchanged.
        self.assertEqual(results[1]["relevance_score"], 4.2)

    def test_preserves_bibliography_for_reference_questions(self):
        bibliography = (
            "Smith. Academic Press, 1999. "
            "Jones. Research Journal, 2004. "
            "Brown. University Press, 2015."
        )

        matches = [
            {"text": bibliography, "relevance_score": 4.2},
            {"text": "Normal passage", "relevance_score": 3.5}
        ]

        results = rerank_for_source_quality(
            "What references are listed?",
            matches
        )

        self.assertEqual(results, matches)

    def test_empty_ranking(self):
        results = rerank_for_source_quality(
            "Test question",
            []
        )

        self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main()
