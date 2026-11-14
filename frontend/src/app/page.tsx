"use client";

import { 
  useEffect, 
  useState, 
  type ChangeEvent,
  type SubmitEvent,
} from "react";
import {
  fetchDocumentStats,
  fetchDocuments,
  deleteDocument,
  uploadDocument,
  searchAllDocuments,
  type DocumentStats,
  type DocumentRecord,
  type SearchMatch,
} from "@/lib/api";

import SearchResultCard from "@/components/SearchResultCard";

export default function Home() {
  const [stats, setStats] =
    useState<DocumentStats | null>(null);

  const [statsError, setStatsError] =
    useState<string | null>(null);

  const [documents, setDocuments] =
    useState<DocumentRecord[]>([]);

  const [documentsLoading, setDocumentsLoading] =
    useState(true);

  const [documentsError, setDocumentsError] =
    useState<string | null>(null);

  const [deletingId, setDeletingId] =
    useState<string | null>(null);

  const [deleteError, setDeleteError] =
    useState<string | null>(null);
  
  const [uploading, setUploading] = useState(false);

  const [uploadMessage, setUploadMessage] =
    useState<string | null>(null);

  const [uploadError, setUploadError] =
    useState<string | null>(null);
  

  const [searchQuestion, setSearchQuestion] =
    useState("");

  const [searching, setSearching] =
    useState(false);

  const [searchResults, setSearchResults] =
    useState<SearchMatch[]>([]);

  const [searchError, setSearchError] =
    useState<string | null>(null);

  const [hasSearched, setHasSearched] =
    useState(false);

  const [maxDistance, setMaxDistance] = useState(0.60);

  const [resultLimit, setResultLimit] = useState(5);

  const [sortBy, setSortBy] = useState<
    "relevance" | "distance"
  >("relevance");

  // Fetch document statistics.
  useEffect(() => {
    const controller = new AbortController();

    async function loadStats() {
      try {
        const data = await fetchDocumentStats(
          controller.signal
        );

        if (!controller.signal.aborted) {
          setStats(data);
        }
      } catch {
        if (!controller.signal.aborted) {
          setStatsError(
            "Unable to load statistics. Check that FastAPI is running."
          );
        }
      }
    }

    void loadStats();

    return () => controller.abort();
  }, []);

  // Fetch indexed documents.
  useEffect(() => {
    const controller = new AbortController();

    async function loadDocuments() {
      try {
        const data = await fetchDocuments(
          controller.signal
        );

        if (!controller.signal.aborted) {
          setDocuments(data.documents);
        }
      } catch {
        if (!controller.signal.aborted) {
          setDocumentsError(
            "Unable to load documents. Check that FastAPI is running."
          );
        }
      } finally {
        if (!controller.signal.aborted) {
          setDocumentsLoading(false);
        }
      }
    }

    void loadDocuments();

    return () => controller.abort();
  }, []);

  // Delete an indexed document after confirmation.
  async function handleDelete(document: DocumentRecord) {
    const confirmed = window.confirm(
      `Are you sure you want to delete "${document.filename}"?\n\n` +
      `Document ID: ${document.document_id}\n\n` +
      "This removes the indexed document and cannot be undone."
    );

    if (!confirmed) {
      return;
    }

    setDeletingId(document.document_id);
    setDeleteError(null);

    try {
      await deleteDocument(document.document_id);

      // Remove the deleted document from the library.
      setDocuments((previousDocuments) =>
        previousDocuments.filter(
          (item) =>
            item.document_id !== document.document_id
        )
      );

      // Refresh statistics after successful deletion.
      try {
        const updatedStats = await fetchDocumentStats();

        setStats(updatedStats);
        setStatsError(null);
      } catch {
        setStats(null);
        setStatsError(
          "Document deleted, but statistics could not be refreshed."
        );
      }
    } catch {
      setDeleteError(
        `Unable to delete "${document.filename}". Please try again.`
      );
    } finally {
      setDeletingId(null);
    }
  }

  async function handleUpload(
    event: ChangeEvent<HTMLInputElement>
  ) {
    const file = event.currentTarget.files?.[0];

    if (!file) {
      return;
    }

    // Allow the same file to be selected again.
    event.currentTarget.value = "";

    setUploadMessage(null);
    setUploadError(null);

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setUploadError("Please select a PDF file.");
      return;
    }

    const maxFileSize = 10 * 1024 * 1024;

    if (file.size > maxFileSize) {
      setUploadError(
        "The PDF must be 10 MB or smaller."
      );
      return;
    }

    setUploading(true);

    try {
      const result = await uploadDocument(file);

      // Refresh the document list and statistics.
      try {
        const [documentData, statsData] =
          await Promise.all([
            fetchDocuments(),
            fetchDocumentStats(),
          ]);

        setDocuments(documentData.documents);
        setStats(statsData);

        setDocumentsError(null);
        setStatsError(null);

        if (result.duplicate) {
          setUploadMessage(
            "This PDF is already indexed. No duplicate was added."
          );
        } else {
          setUploadMessage(
            `"${file.name}" was uploaded and indexed successfully.`
          );
        }
      } catch {
        setUploadMessage(
          "The PDF was processed, but the dashboard could not refresh. Please reload the page."
        );
      }
    } catch {
      setUploadError(
        "Unable to upload the PDF. Check that FastAPI is running and the file is valid."
      );
    } finally {
      setUploading(false);
    }
  }

  async function handleSearch(
    event: SubmitEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    const question = searchQuestion.trim();

    if (!question || searching) {
      return;
    }

    setSearching(true);
    setSearchError(null);
    setSearchResults([]);
    setHasSearched(false);

    try {
      const result = await searchAllDocuments(
        question,
        resultLimit
      );

      setSearchResults(result.matches);
      setHasSearched(true);

    } catch (error) {
      setSearchError(
        error instanceof Error
          ? error.message
          : "Unable to search documents."
      );
    } finally {
      setSearching(false);
    }
  }

  const statCards = [
    {
      label: "Documents",
      value: stats?.total_documents ?? "—",
      description: "Indexed PDF files",
    },
    {
      label: "Text Chunks",
      value: stats?.total_chunks ?? "—",
      description: "Searchable passages",
    },
    {
      label: "Indexed Pages",
      value: stats?.total_indexed_pages ?? "—",
      description: "Pages with extracted text",
    },
  ];

  const visibleResults = searchResults
    .filter(
      (match) =>
        Number.isFinite(match.distance) &&
        match.distance <= maxDistance
    )
    .sort((a, b) => {
      if (sortBy === "distance") {
        return a.distance - b.distance;
      }

      return (
        (b.relevance_score ?? Number.NEGATIVE_INFINITY) -
        (a.relevance_score ?? Number.NEGATIVE_INFINITY)
      );
    });

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
          <div>
            <h1 className="text-xl font-bold tracking-tight">
              Document Q&A Assistant
            </h1>

            <p className="mt-1 text-sm text-slate-500">
              AI-powered document search
            </p>
          </div>

          <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700">
            Dashboard Preview
          </span>
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-8 px-6 py-10">
        {/* Dashboard heading */}
        <section>
          <h2 className="text-2xl font-bold">
            Dashboard
          </h2>

          <p className="mt-2 text-slate-600">
            Manage your documents and find relevant information
            using semantic search.
          </p>
        </section>

        {/* Document statistics */}
        <section className="grid gap-5 md:grid-cols-3">
          {statCards.map((stat) => (
            <div
              key={stat.label}
              className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
            >
              <p className="text-sm font-medium text-slate-500">
                {stat.label}
              </p>

              <p className="mt-3 text-3xl font-bold">
                {stat.value}
              </p>

              <p className="mt-2 text-sm text-slate-500">
                {stat.description}
              </p>
            </div>
          ))}
        </section>

        {/* Statistics status */}
        {statsError ? (
          <p role="alert" className="text-sm text-red-600">
            {statsError}
          </p>
        ) : (
          <p className="text-xs text-slate-500">
            {stats
              ? "Statistics loaded from your FastAPI backend."
              : "Loading document statistics..."}
          </p>
        )}

        <div className="grid gap-6 lg:grid-cols-2">
          
          {/* Upload section */}
          <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="text-lg font-semibold">
              Upload Documents
            </h3>

            <p className="mt-2 text-sm text-slate-500">
              Add PDF files to your searchable document library.
            </p>

            <div className="mt-6 flex min-h-48 flex-col items-center justify-center rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 p-6 text-center">
              <div className="mb-3 text-3xl">
                📄
              </div>

              <p className="font-medium">
                PDF Upload
              </p>

              <p className="mt-2 text-sm text-slate-500">
                Supports PDF documents up to 10 MB.
              </p>

              <label
                htmlFor="pdf-upload"
                className={`mt-4 inline-block rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white ${
                  uploading
                    ? "cursor-not-allowed opacity-50"
                    : "cursor-pointer hover:bg-blue-700"
                }`}
              >
                {uploading ? "Uploading..." : "Choose PDF"}
              </label>

              <input
                id="pdf-upload"
                type="file"
                accept=".pdf,application/pdf"
                disabled={uploading}
                onChange={(event) => void handleUpload(event)}
                className="sr-only"
              />

              {uploading && (
                <p
                  role="status"
                  className="mt-4 text-sm text-blue-600"
                >
                  Uploading and indexing your document...
                </p>
              )}

              {uploadMessage && (
                <p
                  role="status"
                  className="mt-4 text-sm text-green-700"
                >
                  {uploadMessage}
                </p>
              )}

              {uploadError && (
                <p
                  role="alert"
                  className="mt-4 text-sm text-red-600"
                >
                  {uploadError}
                </p>
              )}
            </div>
          </section>
          {/* Semantic search section */}
          <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="text-lg font-semibold">
              Semantic Search
            </h3>

            <p className="mt-2 text-sm text-slate-500">
              Find relevant passages across your uploaded PDFs.
            </p>

            <form
              onSubmit={(event) => void handleSearch(event)}
              className="mt-6 space-y-4"
            >
              <label
                htmlFor="question"
                className="block text-sm font-medium"
              >
                Your question
              </label>

              <textarea
                id="question"
                rows={4}
                value={searchQuestion}
                onChange={(event) =>
                  setSearchQuestion(event.target.value)
                }
                placeholder="Ask a question about your documents..."
                className="w-full resize-none rounded-lg border border-slate-300 bg-white p-3 text-sm placeholder:text-slate-400 focus:border-blue-500 focus:outline-none"
              />

              {/* Advanced Search Settings */}
              <div className="space-y-4 rounded-lg border border-slate-200 bg-slate-50 p-4">
                <h4 className="text-sm font-semibold text-slate-800">
                  Advanced Search Settings
                </h4>

                <div>
                  <label
                    htmlFor="distance-threshold"
                    className="flex justify-between text-sm font-medium"
                  >
                    <span>Maximum cosine distance</span>
                    <span>{maxDistance.toFixed(2)}</span>
                  </label>

                  <input
                    id="distance-threshold"
                    type="range"
                    min="0.30"
                    max="0.90"
                    step="0.05"
                    value={maxDistance}
                    onChange={(event) =>
                      setMaxDistance(Number(event.target.value))
                    }
                    className="mt-3 w-full accent-blue-600"
                  />

                  <p className="mt-1 text-xs text-slate-500">
                    Lower values apply stricter filtering.
                  </p>
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <label
                      htmlFor="result-limit"
                      className="block text-sm font-medium"
                    >
                      Results per search
                    </label>

                    <select
                      id="result-limit"
                      value={resultLimit}
                      onChange={(event) =>
                        setResultLimit(Number(event.target.value))
                      }
                      className="mt-2 w-full rounded-lg border border-slate-300 bg-white p-2 text-sm"
                    >
                      <option value={5}>5 results</option>
                      <option value={10}>10 results</option>
                      <option value={20}>20 results</option>
                    </select>
                  </div>

                  <div>
                    <label
                      htmlFor="sort-results"
                      className="block text-sm font-medium"
                    >
                      Sort results by
                    </label>

                    <select
                      id="sort-results"
                      value={sortBy}
                      onChange={(event) =>
                        setSortBy(
                          event.target.value as "relevance" | "distance"
                        )
                      }
                      className="mt-2 w-full rounded-lg border border-slate-300 bg-white p-2 text-sm"
                    >
                      <option value="relevance">Relevance score</option>
                      <option value="distance">Cosine distance</option>
                    </select>
                  </div>
                </div>
              </div>

              <button
                type="submit"
                disabled={searching || !searchQuestion.trim()}
                className="w-full rounded-lg bg-blue-600 px-4 py-3 font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {searching
                  ? "Searching..."
                  : "Search Documents"}
              </button>
              <button
                type="button"
                disabled={
                  searching ||
                  (!searchQuestion && !hasSearched && !searchError)
                }
                onClick={() => {
                  setSearchQuestion("");
                  setSearchResults([]);
                  setSearchError(null);
                  setHasSearched(false);
                }}
                className="w-full rounded-lg border border-slate-300 bg-white px-4 py-3 font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Clear Search
              </button>
            </form>

            {/* Search loading state */}
            {searching && (
              <p
                role="status"
                className="mt-4 text-sm text-blue-600"
              >
                Searching your indexed documents...
              </p>
            )}

            {/* Search error */}
            {searchError && (
              <p
                role="alert"
                className="mt-4 text-sm text-red-600"
              >
                {searchError}
              </p>
            )}

            {/* Search results */}
            {hasSearched && !searching && (
              <div className="mt-6 space-y-4">
                <h4 className="font-semibold text-slate-800">
                  Search Results ({visibleResults.length} of {searchResults.length})
                </h4>

                {searchResults.length > visibleResults.length && (
                  <p className="text-sm text-amber-700">
                    {searchResults.length - visibleResults.length} passage(s)
                    hidden by the current cosine-distance threshold.
                  </p>
                )}

                {searchResults.length === 0 ? (
                  <p className="text-sm text-slate-500">
                    No passages were returned by the search.
                    Try another question or upload additional PDFs.
                  </p>
                ) : visibleResults.length === 0 ? (
                  <p className="text-sm text-slate-500">
                    All retrieved passages were filtered out.
                    Try increasing the maximum cosine distance.
                  </p>
                ) : (
                  <div className="space-y-4">
                    {visibleResults.map((match) => (
                      <SearchResultCard
                        key={`${match.document_id}-${match.page_number}-${match.text}`}
                        match={match}
                      />
                    ))}
                  </div>
                )}
              </div>
            )}
          </section>
        </div>

        {/* Document Library */}
        <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 className="text-lg font-semibold">
                Document Library
              </h3>

              <p className="mt-2 text-sm text-slate-500">
                View and manage your indexed documents.
              </p>
            </div>

            <span className="rounded-lg bg-blue-50 px-3 py-2 text-xs font-medium text-blue-700">
              {documentsLoading
                ? "Loading..."
                : documentsError
                  ? "Unavailable"
                  : `${documents.length} documents`}
            </span>
          </div>

          {/* Deletion error */}
          {deleteError && (
            <p
              role="alert"
              className="mt-4 text-sm text-red-600"
            >
              {deleteError}
            </p>
          )}

          <div className="mt-6">
            {documentsLoading ? (
              <p className="text-sm text-slate-500">
                Loading documents...
              </p>
            ) : documentsError ? (
              <p
                role="alert"
                className="text-sm text-red-600"
              >
                {documentsError}
              </p>
            ) : documents.length === 0 ? (
              <div className="rounded-lg border border-slate-200 bg-slate-50 p-8 text-center">
                <p className="font-medium text-slate-700">
                  No documents uploaded yet
                </p>

                <p className="mt-2 text-sm text-slate-500">
                  Upload a PDF to get started.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {documents.map((document) => (
                  <div
                    key={document.document_id}
                    className="flex flex-wrap items-center justify-between gap-4 rounded-lg border border-slate-200 p-4"
                  >
                    <div className="min-w-0">
                      <p className="break-all font-medium text-slate-800">
                        📄 {document.filename}
                      </p>

                      <p className="mt-2 text-sm text-slate-500">
                        {document.indexed_pages} pages
                        {" • "}
                        {document.total_chunks} chunks
                      </p>
                    </div>

                    <div className="flex items-center gap-3">
                      <span className="rounded-full bg-green-50 px-3 py-1 text-xs font-medium text-green-700">
                        Indexed
                      </span>

                      <button
                        type="button"
                        onClick={() => void handleDelete(document)}
                        disabled={deletingId !== null}
                        className="rounded-lg border border-red-200 px-3 py-2 text-sm font-medium text-red-600 transition hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        {deletingId === document.document_id
                          ? "Deleting..."
                          : "Delete"}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-200 bg-white py-6 text-center text-sm text-slate-500">
        AI Document Q&A Assistant
      </footer>
    </div>
  );
}
