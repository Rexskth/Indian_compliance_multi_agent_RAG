import { QueryRequest, QueryResponse, HealthResponse } from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function sendQuery(request: QueryRequest): Promise<QueryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

export type StreamCallback = (data: {
  stage?: string;
  message?: string;
  answer?: string;
  citations?: any[];
  risk_level?: string;
  severity_score?: number;
  risk_details?: any;
  confidence?: number;
  intent?: string;
  sources?: string[];
  cache_hit?: boolean;
  cache_type?: string;
}) => void;

export async function sendQueryStream(
  request: QueryRequest,
  onStage: StreamCallback,
  onComplete: (result: QueryResponse) => void,
  onError: (error: Error) => void
): Promise<void> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/query/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    if (!reader) {
      throw new Error("No response body");
    }

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data = JSON.parse(line.slice(6));
          
          if (data.stage === "complete") {
            onComplete({
              answer: data.answer,
              citations: data.citations,
              risk_level: data.risk_level,
              severity_score: data.severity_score,
              risk_details: data.risk_details,
              confidence: data.confidence,
              intent: data.intent,
              sources: data.sources,
            });
          } else {
            onStage(data);
          }
        }
      }
    }
  } catch (err) {
    onError(err instanceof Error ? err : new Error("Unknown error"));
  }
}

export async function checkHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/health`);

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

export async function getMetrics() {
  const response = await fetch(`${API_BASE_URL}/api/metrics`);

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}