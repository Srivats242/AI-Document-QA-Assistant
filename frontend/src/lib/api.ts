const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000";

export type DocumentStats = {
  total_documents: number;
  total_chunks: number;
  total_indexed_pages: number;
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
