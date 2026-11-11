from uuid import uuid4

import pymupdf
from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel, Field

from document_processor import chunk_document
from vector_store import (
    store_document,
    search_document,
    list_documents,
    get_document_info,
    delete_document
)

app = FastAPI(
    title="AI Document Q&A Assistant",
    description="Document processing and semantic search API",
    version="0.3.0"
)

MAX_FILE_SIZE = 10 * 1024 * 1024


class SearchRequest(BaseModel):
    document_id: str
    question: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=20)


@app.get("/")
def home():
    return {"message": "AI Document Q&A Assistant is running!"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )

    try:
        pdf_bytes = await file.read(MAX_FILE_SIZE + 1)

        if len(pdf_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="PDF exceeds the 10 MB limit"
            )

        if not pdf_bytes.startswith(b"%PDF-"):
            raise HTTPException(
                status_code=400,
                detail="Invalid PDF file"
            )

        pages = []

        with pymupdf.open(stream=pdf_bytes, filetype="pdf") as document:
            if document.needs_pass:
                raise HTTPException(
                    status_code=400,
                    detail="Password-protected PDFs are not supported"
                )

            for page_index, page in enumerate(document):
                pages.append({
                    "page_number": page_index + 1,
                    "text": page.get_text("text")
                })

        chunks = chunk_document(pages)

        if not chunks:
            raise HTTPException(
                status_code=422,
                detail="No extractable text found in PDF"
            )

        document_id = str(uuid4())

        stored_count = store_document(
            document_id,
            file.filename or "document.pdf",
            chunks
        )

        return {
            "document_id": document_id,
            "filename": file.filename,
            "total_pages": len(pages),
            "total_chunks": stored_count,
            "message": "Document processed and indexed"
        }

    except HTTPException:
        raise

    except (pymupdf.FileDataError, pymupdf.EmptyFileError):
        raise HTTPException(
            status_code=400,
            detail="Could not read the PDF"
        )

    finally:
        await file.close()


@app.get("/documents")
def get_documents():
    documents = list_documents()

    return {
        "count": len(documents),
        "documents": documents
    }


@app.get("/documents/{document_id}")
def get_document(document_id: str):
    document = get_document_info(document_id)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    return document


@app.delete("/documents/{document_id}")
def remove_document(document_id: str):
    deleted_count = delete_document(document_id)

    if deleted_count is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    return {
        "document_id": document_id,
        "deleted_chunks": deleted_count,
        "message": "Document deleted successfully"
    }


@app.post("/search")
def search(request: SearchRequest):
    matches = search_document(
        document_id=request.document_id,
        question=request.question,
        limit=request.limit
    )

    if not matches:
        raise HTTPException(
            status_code=404,
            detail="No indexed passages found for this document"
        )

    return {
        "document_id": request.document_id,
        "question": request.question,
        "matches": matches
    }
