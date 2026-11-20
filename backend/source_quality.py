import re


def is_bibliography_heavy(text: str) -> bool:
    """Detect passages dominated by bibliographic references."""

    if not text or not text.strip():
        return False

    # Look for publication years commonly found in references.
    publication_years = re.findall(
        r"\b(?:18|19|20)\d{2}\b",
        text
    )

    # Look for common academic citation indicators.
    citation_indicators = re.findall(
        r"\b(?:press|journal|publisher|edited by)\b|\beds?\.",
        text,
        flags=re.IGNORECASE
    )

    return (
        len(publication_years) >= 3
        and len(citation_indicators) >= 2
    )


def rerank_for_source_quality(question, matches):
    """Apply a small penalty to bibliography-heavy passages."""

    if not matches:
        return []

    # Reference-related questions should still retrieve bibliographies.
    reference_question = re.search(
        r"\b(?:bibliography|bibliographies|references|"
        r"works cited|citations|cited sources|sources cited)\b",
        question,
        flags=re.IGNORECASE
    )

    if reference_question:
        return matches

    bibliography_penalty = 2.0

    def adjusted_score(match):
        score = match.get("relevance_score", 0.0)

        if is_bibliography_heavy(match.get("text", "")):
            score -= bibliography_penalty

        return score

    return sorted(
        matches,
        key=adjusted_score,
        reverse=True
    )
