import type { AnalyzeRequest, AnalyzeResponse } from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export async function analyzeTrip(
  req: AnalyzeRequest,
  signal?: AbortSignal
): Promise<AnalyzeResponse> {
  const res = await fetch(`${API_BASE}/api/v1/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
    signal,
  });
  if (!res.ok) {
    let detail = `Ошибка сервера (${res.status})`;
    try {
      const data = await res.json();
      if (typeof data.detail === "string") detail = data.detail;
      else if (Array.isArray(data.detail)) {
        detail = data.detail
          .map((e: { msg?: string }) => e.msg ?? JSON.stringify(e))
          .join("; ");
      }
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<AnalyzeResponse>;
}
