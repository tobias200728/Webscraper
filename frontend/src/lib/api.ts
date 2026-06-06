import { SearchParams, Vehicle } from "@/types/vehicle";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function* streamSearch(
  params: SearchParams,
  signal?: AbortSignal,
): AsyncGenerator<Vehicle> {
  const resp = await fetch(`${API_BASE}/search/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
    signal,
  });

  if (!resp.ok) throw new Error(`HTTP ${resp.status}: ${resp.statusText}`);
  if (!resp.body) throw new Error("Keine Antwort vom Server");

  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const raw = line.slice(6).trim();
      if (!raw) continue;
      try {
        const obj = JSON.parse(raw);
        if ("total" in obj) return; // done-event
        yield obj as Vehicle;
      } catch {
        // ungültige Zeile überspringen
      }
    }
  }
}

export async function getSources(): Promise<string[]> {
  const resp = await fetch(`${API_BASE}/search/sources`);
  const data = await resp.json();
  return data.sources ?? [];
}
