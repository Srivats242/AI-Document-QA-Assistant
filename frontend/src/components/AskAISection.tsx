"use client";

import { useState, type SubmitEvent } from "react";
import { askQuestion, type AskResponse } from "@/lib/api";

export default function AskAISection() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<AskResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleAsk(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmedQuestion = question.trim();

    if (!trimmedQuestion || loading) {
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await askQuestion(trimmedQuestion, 5);
      setResult(response);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to generate an AI answer."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <h3 className="text-lg font-semibold">
        Ask AI About Your Documents
      </h3>

      <p className="mt-2 text-sm text-slate-500">
        Generate answers using passages from your uploaded PDFs.
      </p>

      <form
        onSubmit={(event) => void handleAsk(event)}
        className="mt-6 space-y-4"
      >
        <label
          htmlFor="ai-question"
          className="block text-sm font-medium"
        >
          Your question
        </label>

        <textarea
          id="ai-question"
          rows={3}
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="What would you like to know about your documents?"
          className="w-full resize-none rounded-lg border border-slate-300 p-3 text-sm focus:border-blue-500 focus:outline-none"
        />

        <button
          type="submit"
          disabled={loading || !question.trim()}
          className="rounded-lg bg-blue-600 px-6 py-3 font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? "Generating Answer..." : "Ask AI"}
        </button>
      </form>

      {loading && (
        <p role="status" className="mt-4 text-sm text-blue-600">
          Searching documents and generating an answer...
        </p>
      )}

      {error && (
        <p role="alert" className="mt-4 text-sm text-red-600">
          {error}
        </p>
      )}

      {result && (
        <div className="mt-6 space-y-5">
          <div className="rounded-lg border border-blue-100 bg-blue-50 p-5">
            <h4 className="font-semibold text-slate-800">
              AI-Generated Answer
            </h4>

            <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-slate-700">
              {result.answer}
            </p>
          </div>

          <div>
            <h4 className="font-semibold text-slate-800">
              Sources ({result.total_sources})
            </h4>

            <div className="mt-3 space-y-3">
              {result.sources.map((source, index) => (
                <div
                  key={`${source.document_id}-${source.page_number}-${index}`}
                  className="rounded-lg border border-slate-200 p-4"
                >
                  <p className="text-sm font-medium text-slate-800">
                    {source.citation} {source.filename}
                    {" — "}Page {source.page_number}
                  </p>

                  <p className="mt-2 whitespace-pre-wrap text-sm text-slate-600">
                    {source.text}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
