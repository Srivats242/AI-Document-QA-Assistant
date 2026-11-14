"use client";

import { useState } from "react";
import type { SearchMatch } from "@/lib/api";

type Props = {
  match: SearchMatch;
};

const PREVIEW_LENGTH = 320;

export default function SearchResultCard({ match }: Props) {
  const [expanded, setExpanded] = useState(false);

  const isLong = match.text.length > PREVIEW_LENGTH;

  const displayedText =
    isLong && !expanded
      ? `${match.text.slice(0, PREVIEW_LENGTH).trimEnd()}...`
      : match.text;

  return (
    <article className="rounded-lg border border-slate-200 bg-slate-50 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="break-all text-sm font-semibold text-slate-800">
          📄 {match.filename}
        </p>

        <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700">
          Page {match.page_number}
        </span>
      </div>

      <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-slate-700">
        {displayedText}
      </p>

      {isLong && (
        <button
          type="button"
          aria-expanded={expanded}
          onClick={() => setExpanded(!expanded)}
          className="mt-3 text-sm font-medium text-blue-600 hover:text-blue-800"
        >
          {expanded ? "Show Less" : "Show More"}
        </button>
      )}

      <div className="mt-4 border-t border-slate-200 pt-3">
        <p className="text-xs text-slate-500">
          Cosine distance: {match.distance.toFixed(3)}
        </p>

        {typeof match.relevance_score === "number" && (
          <p className="mt-1 text-xs text-slate-500">
            Relevance score: {match.relevance_score.toFixed(2)}
          </p>
        )}
      </div>
    </article>
  );
}
