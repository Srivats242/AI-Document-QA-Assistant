# AI Document Q&A Assistant

A document question-answering project built with Python and FastAPI. The application allows users to upload PDF documents, extract and process their text, and perform semantic searches to retrieve passages relevant to their questions.

## Features

- **PDF Upload:** Upload PDF documents through a FastAPI endpoint.
- **Text Extraction:** Extract text from PDFs using PyMuPDF.
- **Document Chunking:** Split extracted text into smaller, overlapping chunks.
- **Text Embeddings:** Generate vector embeddings using Sentence Transformers.
- **Semantic Search:** Retrieve relevant document passages using ChromaDB.
- **Source References:** Return page numbers alongside retrieved passages.
- **Input Validation:** Validate PDF file types, file sizes, and document contents.

## Tech Stack

- **Python** — Backend programming language
- **FastAPI** — REST API framework
- **PyMuPDF** — PDF text extraction
- **Sentence Transformers** — Text embedding generation
- **ChromaDB** — Persistent vector database
- **Pydantic** — API request validation
- **Uvicorn** — ASGI web server
- **unittest** — Automated unit testing

## Project Structure

```text
ai-document-assistant/
├── .gitignore
├── README.md
└── backend/
    ├── main.py
    ├── document_processor.py
    ├── vector_store.py
    ├── test_document_processor.py
    └── requirements.txt
```

The application also creates a local `chroma_db` directory for persistent vector storage.

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Srivats242/AI-Document-QA-Assistant.git
cd AI-Document-QA-Assistant/backend
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Start the application

```bash
python -m uvicorn main:app --reload
```

Open the interactive API documentation:

http://127.0.0.1:8000/docs

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Check whether the application is running |
| GET | `/health` | Return application health status |
| POST | `/upload` | Upload, process, and index a PDF |
| POST | `/search` | Search indexed document passages |

### Upload a PDF

Use `POST /upload` to upload a PDF document.

The endpoint extracts text, divides it into chunks, generates embeddings, and stores them in ChromaDB.

The response includes a unique document ID, filename, total page count, and total chunk count.

### Search a document

Use `POST /search` with a JSON request:

```json
{
  "document_id": "YOUR_DOCUMENT_ID",
  "question": "What are the main findings of this document?",
  "limit": 3
}
```

The response returns relevant passages, their source page numbers, and similarity distances.

## Testing

Run the document-processing unit tests from the `backend` directory:

```bash
python -m unittest -v test_document_processor
```

The tests cover text cleaning, empty documents, short and long documents, and invalid chunking parameters.

## Current Scope

The application supports PDF processing and semantic retrieval. The search endpoint returns relevant source passages rather than generating natural-language answers.