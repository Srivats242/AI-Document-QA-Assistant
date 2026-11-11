const stats = [
  {
    label: "Documents",
    value: "4",
    description: "Indexed PDF files",
  },
  {
    label: "Text Chunks",
    value: "369",
    description: "Searchable passages",
  },
  {
    label: "Indexed Pages",
    value: "88",
    description: "Pages with extracted text",
  },
];

export default function Home() {
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
        <section>
          <h2 className="text-2xl font-bold">
            Dashboard
          </h2>
          <p className="mt-2 text-slate-600">
            Manage your documents and find relevant information
            using semantic search.
          </p>
        </section>

        <section className="grid gap-5 md:grid-cols-3">
          {stats.map((stat) => (
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

        <p className="text-xs text-slate-500">
          Statistics are currently static. Live backend integration
          is coming next.
        </p>

        <div className="grid gap-6 lg:grid-cols-2">
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

              <p className="mt-4 text-xs text-slate-400">
                Upload functionality coming soon
              </p>
            </div>
          </section>

          <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="text-lg font-semibold">
              Semantic Search
            </h3>

            <p className="mt-2 text-sm text-slate-500">
              Find relevant passages across your uploaded PDFs.
            </p>

            <div className="mt-6 space-y-4">
              <label
                htmlFor="question"
                className="block text-sm font-medium"
              >
                Your question
              </label>

              <textarea
                id="question"
                rows={4}
                disabled
                placeholder="Ask a question about your documents..."
                className="w-full resize-none rounded-lg border border-slate-300 bg-slate-50 p-3 text-sm placeholder:text-slate-400"
              />

              <button
                type="button"
                disabled
                className="w-full cursor-not-allowed rounded-lg bg-blue-600 px-4 py-3 font-medium text-white opacity-60"
              >
                Search Documents
              </button>

              <p className="text-xs text-slate-400">
                Search functionality coming soon
              </p>
            </div>
          </section>
        </div>

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

            <span className="rounded-lg bg-slate-100 px-3 py-2 text-xs text-slate-500">
              API integration pending
            </span>
          </div>

          <div className="mt-6 rounded-lg border border-slate-200 bg-slate-50 p-8 text-center">
            <p className="font-medium text-slate-700">
              Your documents will appear here
            </p>

            <p className="mt-2 text-sm text-slate-500">
              We will connect this section to the FastAPI
              /documents endpoint.
            </p>
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-200 bg-white py-6 text-center text-sm text-slate-500">
        AI Document Q&A Assistant
      </footer>
    </div>
  );
}
