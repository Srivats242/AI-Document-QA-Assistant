"use client";

import { useRef, useState, type SubmitEvent } from "react";
import ReactMarkdown from "react-markdown";
import { SKIP, visit } from "unist-util-visit";
import type { Root, PhrasingContent } from "mdast";
import { askQuestion, type AskResponse } from "@/lib/api";

// Convert citation text nodes into Markdown links.
// Existing links and inline code are left unchanged.
function createCitationPlugin(validCitations: Set<string>) {
  return function remarkCitations() {
    return (tree: Root) => {
      visit(tree, (node, index, parent) => {
        // Don't modify citations inside existing links.
        if (
          node.type === "link" ||
          node.type === "linkReference"
        ) {
          return SKIP;
        }

        if (
          node.type !== "text" ||
          !parent ||
          index === undefined
        ) {
          return;
        }

        const replacements: PhrasingContent[] = [];
        const citationPattern = /\[(\d+)\]/g;
        let lastIndex = 0;

        for (const match of node.value.matchAll(citationPattern)) {
          const citation = match[0];

          // Only link citations that correspond to real sources.
          if (!validCitations.has(citation)) {
            continue;
          }

          const matchIndex = match.index;

          if (matchIndex > lastIndex) {
            replacements.push({
              type: "text",
              value: node.value.slice(lastIndex, matchIndex),
            });
          }

          replacements.push({
            type: "link",
            url: `#citation-${match[1]}`,
            children: [
              {
                type: "text",
                value: citation,
              },
            ],
          });

          lastIndex = matchIndex + citation.length;
        }

        if (replacements.length === 0) {
          return;
        }

        if (lastIndex < node.value.length) {
          replacements.push({
            type: "text",
            value: node.value.slice(lastIndex),
          });
        }

        const siblings = parent.children as PhrasingContent[];

        siblings.splice(index, 1, ...replacements);

        // Continue after the inserted nodes.
        return index + replacements.length;
      });
    };
  };
}

export default function AskAISection() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<AskResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedCitation, setSelectedCitation] = useState<
    string | null
  >(null);

  const sourceRefs = useRef<Record<string, HTMLDivElement | null>>(
    {}
  );

  function handleCitationClick(citation: string) {
    setSelectedCitation(citation);

    const sourceElement = sourceRefs.current[citation];

    if (sourceElement) {
      sourceElement.focus({ preventScroll: true });
      sourceElement.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    }
  }

  async function handleAsk(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmedQuestion = question.trim();

    if (!trimmedQuestion || loading) {
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setSelectedCitation(null);
    sourceRefs.current = {};

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

  const validCitations = new Set(
    result?.sources.map((source) => source.citation) ?? []
  );

  const citationPlugin = createCitationPlugin(validCitations);

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

            <div className="mt-3 text-sm text-slate-700">
              <ReactMarkdown
                remarkPlugins={[citationPlugin]}
                components={{
                  p: ({ children }) => (
                    <p className="my-3 leading-7">
                      {children}
                    </p>
                  ),
                  ul: ({ children }) => (
                    <ul className="my-3 list-disc space-y-2 pl-6">
                      {children}
                    </ul>
                  ),
                  ol: ({ children }) => (
                    <ol className="my-3 list-decimal space-y-2 pl-6">
                      {children}
                    </ol>
                  ),
                  li: ({ children }) => (
                    <li className="leading-7">
                      {children}
                    </li>
                  ),
                  h1: ({ children }) => (
                    <h1 className="my-3 text-xl font-bold">
                      {children}
                    </h1>
                  ),
                  h2: ({ children }) => (
                    <h2 className="my-3 text-lg font-bold">
                      {children}
                    </h2>
                  ),
                  h3: ({ children }) => (
                    <h3 className="my-3 font-semibold">
                      {children}
                    </h3>
                  ),
                  strong: ({ children }) => (
                    <strong className="font-semibold">
                      {children}
                    </strong>
                  ),
                  blockquote: ({ children }) => (
                    <blockquote className="my-3 border-l-4 border-slate-300 pl-4 italic">
                      {children}
                    </blockquote>
                  ),
                  code: ({ children }) => (
                    <code className="rounded bg-slate-200 px-1 py-0.5 font-mono text-xs">
                      {children}
                    </code>
                  ),
                  a: ({ href, children }) => {
                    const citationMatch = href?.match(
                      /^#citation-(\d+)$/
                    );

                    if (citationMatch) {
                      const citation = `[${citationMatch[1]}]`;

                      const source = result.sources.find(
                        (item) => item.citation === citation
                      );

                      if (source) {
                        return (
                          <button
                            type="button"
                            onClick={() =>
                              handleCitationClick(citation)
                            }
                            aria-label={`Jump to source ${citation}: ${source.filename}, page ${source.page_number}`}
                            className="mx-0.5 rounded font-semibold text-blue-600 underline underline-offset-2 hover:text-blue-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
                          >
                            {children}
                          </button>
                        );
                      }
                    }

                    return (
                      <a
                        href={href}
                        className="text-blue-600 underline hover:text-blue-800"
                      >
                        {children}
                      </a>
                    );
                  },
                }}
              >
                {result.answer}
              </ReactMarkdown>
            </div>
          </div>

          <div>
            <h4 className="font-semibold text-slate-800">
              Sources ({result.total_sources})
            </h4>

            <div className="mt-3 space-y-3">
              {result.sources.map((source, index) => (
                <div
                  key={`${source.document_id}-${source.page_number}-${index}`}
                  ref={(element) => {
                    sourceRefs.current[source.citation] = element;
                  }}
                  tabIndex={-1}
                  className={`rounded-lg border p-4 transition-colors duration-300 focus:outline-none ${
                    selectedCitation === source.citation
                      ? "border-blue-400 bg-blue-50 ring-2 ring-blue-200"
                      : "border-slate-200 bg-white"
                  }`}
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
