export interface QueryRequest {
  query: string;
  conversation_history?: ConversationMessage[];
}

export interface ConversationMessage {
  role: "user" | "assistant";
  content: string;
}

export interface QueryResponse {
  answer: string;
  citations: Citation[];
  risk_level: string;
  severity_score: number;
  risk_details: RiskDetails;
  confidence: number;
  intent: string;
  sources: string[];
}

export interface Citation {
  source: string;
  document_name: string;
  section: string;
  page: number;
  text_preview: string;
}

export interface RiskDetails {
  penalties: string[];
  mitigations: string[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  citations?: Citation[];
  risk_level?: string;
  confidence?: number;
}

export interface HealthResponse {
  status: string;
  version: string;
  collection_count: number;
}