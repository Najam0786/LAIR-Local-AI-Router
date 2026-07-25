export type ChatRole = "system" | "user" | "assistant"

export type Provenance = "measured" | "community" | "declared" | "heuristic" | "memory"

export interface ChatMessage {
  role: ChatRole
  content: string
}

export interface LairMeta {
  model_used: string
  estimated_savings_usd: number | null
  cache_hit: boolean
  routed_to_cloud: boolean
  cloud_escalation_reason: string | null
  memory_injected_count: number
}

export interface Usage {
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
}

export interface ChatCompletionResponse {
  id: string
  model: string
  choices: { message: { role: string; content: string }; finish_reason: string | null }[]
  usage: Usage
  lair_meta: LairMeta | null
}

export interface ChatCompletionChunk {
  id: string
  model: string
  choices: { delta: { role?: string; content?: string }; finish_reason: string | null }[]
  lair_meta: LairMeta | null
}

export interface SavingsResponse {
  day_usd: number
  month_usd: number
  lifetime_usd: number
}

export interface DocumentSummary {
  document_id: string
  filename: string
  chunk_count: number
}

export interface DocumentListResponse {
  documents: DocumentSummary[]
}

export interface DocumentIngestResponse {
  document_id: string
  filename: string
  chunk_count: number
}

export interface TranscriptionResponse {
  text: string
  language: string | null
}

/** A chat turn as rendered in the UI -- distinct from the wire ChatMessage:
 * carries per-turn LAIR metadata and a streaming flag the API never sees. */
export interface DisplayMessage {
  id: string
  role: ChatRole
  content: string
  streaming?: boolean
  meta?: LairMeta | null
  viaVoice?: boolean
}
