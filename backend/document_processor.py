import re
import unicodedata

def clean_text(text):
    # Normalize Unicode characters
    text = unicodedata.normalize("NFC", text)

    # Replace common PDF ligatures with regular letters
    ligatures = {
        "ﬀ": "ff",
        "ﬁ": "fi",
        "ﬂ": "fl",
        "ﬃ": "ffi",
        "ﬄ": "ffl"
    }

    for ligature, replacement in ligatures.items():
        text = text.replace(ligature, replacement)

    # Remove invisible formatting characters
    text = text.replace("\u00ad", "")
    text = text.replace("\u200b", "")
    text = text.replace("\ufeff", "")

    # Replace unwanted control characters with spaces
    text = re.sub(
        r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]",
        " ",
        text
    )

    # Normalize repeated whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def chunk_document(pages, chunk_size=800, overlap=150):
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("Invalid overlap")

    chunks = []

    for page in pages:
        text = clean_text(page["text"])

        if not text:
            continue

        start = 0

        while start < len(text):
            end = min(start + chunk_size, len(text))

            chunk = text[start:end].strip()

            if chunk:
                chunks.append({
                    "page_number": page["page_number"],
                    "text": chunk
                })

            if end == len(text):
                break

            start = end - overlap

    return chunks
