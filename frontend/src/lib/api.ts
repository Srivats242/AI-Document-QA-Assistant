const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000";

export type DocumentStats = {
  total_documents: number;
  total_chunks: number;
  total_indexed_pages: number;
};

export type DocumentRecord = {
  document_id: string;
  filename: string;
  total_chunks: number;
  indexed_pages: number;
};

export type DocumentsResponse = {
  count: number;
  documents: DocumentRecord[];
};

export async function fetchDocumentStats(
  signal?: AbortSignal
): Promise<DocumentStats> {
  const response = await fetch(
    `${API_BASE_URL}/stats`,
    { signal }
  );

  if (!response.ok) {
    throw new Error(
      `Failed to fetch statistics: ${response.status}`
    );
  }

  return response.json();
}

export async function fetchDocuments(
  signal?: AbortSignal
): Promise<DocumentsResponse> {
  const response = await fetch(
    `${API_BASE_URL}/documents`,
    { signal }
  );

  if (!response.ok) {
    throw new Error(
      `Failed to fetch documents: ${response.status}`
    );
  }

  return response.json();
}


export async function deleteDocument(
  documentId: string
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/documents/${encodeURIComponent(documentId)}`,
    {
      method: "DELETE",
    }
  );

  if (!response.ok) {
    throw new Error(
      `Failed to delete document: ${response.status}`
    );
  }
}


export type UploadResponse = {
  document_id: string;
  duplicate?: boolean;
};

export async function uploadDocument(
  file: File
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(
    `${API_BASE_URL}/upload`,
    {
      method: "POST",
      body: formData,
    }
  );

  if (!response.ok) {
    throw new Error(
      `Failed to upload document: ${response.status}`
    );
  }

  return response.json();
}


export type SearchMatch = {
  document_id: string;
  filename: string;
  page_number: number;
  text: string;
  distance: number;
  relevance_score: number;
};

export type SearchResponse = {
  question: string;
  total_matches: number;
  matches: SearchMatch[];
};

export async function searchAllDocuments(
  question: string,
  limit: number = 5
): Promise<SearchResponse> {
  const response = await fetch(
    `${API_BASE_URL}/search/all`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        question,
        limit,
      }),
    }
  );

  if (!response.ok) {
    const errorData = await response
      .json()
      .catch(() => null);

    throw new Error(
      errorData?.detail ??
        `Search failed: ${response.status}`
    );
  }

  return response.json();
}

