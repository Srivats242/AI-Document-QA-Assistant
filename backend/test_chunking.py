
from document_processor import chunk_document

pages = [
    {
        "page_number": 1,
        "text": "Artificial intelligence helps analyze documents. " * 30
    },
    {
        "page_number": 2,
        "text": "Machine learning enables semantic search. " * 30
    }
]

chunks = chunk_document(pages)

print("Total chunks:", len(chunks))

for index, chunk in enumerate(chunks):
    print(
        f"Chunk {index + 1}: "
        f"Page {chunk['page_number']}, "
        f"{len(chunk['text'])} characters"
    )
