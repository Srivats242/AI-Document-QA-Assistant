import re


def clean_text(text):
    # Remove unwanted control characters
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text)
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
