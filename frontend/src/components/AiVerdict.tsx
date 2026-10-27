"use client";

import { Sparkles, Bot } from "lucide-react";
import type { AnalyzeResponse } from "@/lib/types";

/** Простейший рендерер markdown (заголовки ##/###, списки -, **bold**) без внешних зависимостей. */
function renderInline(text: string): React.ReactNode[] {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((p, i) =>
    p.startsWith("**") && p.endsWith("**") ? (
      <strong key={i}>{p.slice(2, -2)}</strong>
    ) : (
      <span key={i}>{p}</span>
    )
  );
}

export default function AiVerdict({ data }: { data: AnalyzeResponse }) {
  const lines = (data.ai_verdict_md ?? "").split(/\r?\n/);
  const nodes: React.ReactNode[] = [];
  let listBuf: string[] = [];

  const flushList = (key: string) => {
    if (listBuf.length) {
      nodes.push(
        <ul key={key}>
          {listBuf.map((li, j) => (
            <li key={j}>{renderInline(li)}</li>
          ))}
        </ul>
      );
      listBuf = [];
    }
  };

  lines.forEach((raw, idx) => {
    const line = raw.trimEnd();
    if (/^[-•*]\s+/.test(line.trim())) {
      listBuf.push(line.trim().replace(/^[-•*]\s+/, ""));
      return;
    }
    flushList(`ul-${idx}`);
    const t = line.trim();
    if (!t) return;
    if (t.startsWith("### ")) {
      nodes.push(<h3 key={idx}>{renderInline(t.slice(4))}</h3>);
    } else if (t.startsWith("## ")) {
      nodes.push(
        <h2 key={idx}>
          <Sparkles size={16} className="text-indigo-500" />
          {renderInline(t.slice(3))}
        </h2>
      );
    } else if (t.startsWith("# ")) {
      nodes.push(<h2 key={idx}>{renderInline(t.slice(2))}</h2>);
    } else {
      nodes.push(<p key={idx}>{renderInline(t)}</p>);
    }
  });
  flushList("ul-last");

  return (
    <div className="card">
      <h3 className="mb-3 flex items-center gap-2 text-lg font-bold">
        <Bot size={18} className="text-indigo-500" /> AI-вердикт
        <span className="rounded-full bg-slate-500/10 px-2 py-0.5 text-[10px] font-medium muted">
          {data.ai_source === "llm" ? "LLM" : "правила"}
        </span>
      </h3>
      <div className="ai-md text-sm">{nodes}</div>
    </div>
  );
}
