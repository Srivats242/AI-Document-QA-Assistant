import re


def clean_extracted_text(text: str) -> str:
    if not text:
        return ""

    # Normalize line endings.
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove invisible soft hyphens.
    text = text.replace("\u00ad", "")

    # Replace non-breaking spaces with regular spaces.
    text = text.replace("\u00a0", " ")

    # Join words split by a hyphen at a line break.
    text = re.sub(
        r"(?<=[A-Za-z])-[ \t]*\n[ \t]*(?=[a-z])",
        "",
        text,
    )

    # Remove unnecessary spaces and tabs.
    text = re.sub(r"[ \t]+", " ", text)

    # Remove spaces surrounding newlines.
    text = re.sub(r" *\n *", "\n", text)

    # Reduce excessive blank lines.
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
