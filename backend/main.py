
from fastapi import FastAPI, File, UploadFile, HTTPException
import pymupdf

app = FastAPI(
    title="AI Document Q&A Assistant",
    description="Backend API for document-based AI question answering",
    version="0.2.0"
)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@app.get("/")
def home():
    return {
        "message": "AI Document Q&A Assistant is running!"
    }


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

        with pymupdf.open(
            stream=pdf_bytes,
            filetype="pdf"
        ) as document:

            if document.needs_pass:
                raise HTTPException(
                    status_code=400,
                    detail="Password-protected PDFs are not supported"
                )

            for page_index, page in enumerate(document):
                text = page.get_text("text")

                pages.append({
                    "page_number": page_index + 1,
                    "text": text.strip()
                })

        return {
            "filename": file.filename,
            "total_pages": len(pages),
            "pages": pages
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
