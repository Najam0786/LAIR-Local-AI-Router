import type {
  ChatCompletionChunk,
  ChatMessage,
  DocumentIngestResponse,
  DocumentListResponse,
  SavingsResponse,
  TranscriptionResponse,
} from "./types"

export interface StreamChatOptions {
  noCache?: boolean
  documentId?: string | null
  projectScope?: string | null
  signal?: AbortSignal
}

export interface StreamChatDelta {
  content: string
  modelId: string
  meta: ChatCompletionChunk["lair_meta"]
  done: boolean
}

/**
 * Streams a chat completion, yielding one delta per SSE chunk. Mirrors
 * the parsing tests already exercise server-side (`_parse_sse_lines`
 * in tests/test_api_chat.py) but on the browser's ReadableStream.
 */
export async function* streamChat(
  messages: ChatMessage[],
  options: StreamChatOptions = {},
): AsyncGenerator<StreamChatDelta> {
  const response = await fetch("/v1/chat/completions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    signal: options.signal,
    body: JSON.stringify({
      messages,
      stream: true,
      lair_no_cache: options.noCache ?? false,
      lair_document_id: options.documentId ?? null,
      lair_project_scope: options.projectScope ?? null,
    }),
  })

  if (!response.ok || !response.body) {
    const detail = await response.text()
    throw new Error(detail || `Chat request failed (${response.status})`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""

  while (true) {
    const { value, done } = await reader.read()

    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split("\n\n")
    buffer = lines.pop() ?? ""

    for (const line of lines) {
      const payload = line.replace(/^data: /, "").trim()

      if (!payload) continue

      if (payload === "[DONE]") {
        yield { content: "", modelId: "", meta: null, done: true }
        return
      }

      const chunk: ChatCompletionChunk = JSON.parse(payload)
      const delta = chunk.choices[0]?.delta

      yield {
        content: delta?.content ?? "",
        modelId: chunk.model,
        meta: chunk.lair_meta,
        done: false,
      }
    }
  }
}

export async function listModels(): Promise<string[]> {
  const response = await fetch("/v1/models")
  const body = await response.json()
  return (body.data ?? []).map((m: { id: string }) => m.id)
}

export async function getSavings(): Promise<SavingsResponse> {
  const response = await fetch("/v1/lair/savings")
  return response.json()
}

export async function listDocuments(): Promise<DocumentListResponse> {
  const response = await fetch("/v1/lair/documents")
  return response.json()
}

export async function uploadDocument(file: File): Promise<DocumentIngestResponse> {
  const form = new FormData()
  form.append("file", file)

  const response = await fetch("/v1/lair/documents", { method: "POST", body: form })

  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || `Upload failed (${response.status})`)
  }

  return response.json()
}

export async function forgetDocument(documentId: string): Promise<void> {
  await fetch(`/v1/lair/documents/${documentId}`, { method: "DELETE" })
}

export async function transcribeAudio(blob: Blob): Promise<TranscriptionResponse> {
  const form = new FormData()
  form.append("file", blob, "recording.webm")

  const response = await fetch("/v1/audio/transcriptions", {
    method: "POST",
    body: form,
  })

  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || `Transcription failed (${response.status})`)
  }

  return response.json()
}

export async function synthesizeSpeech(text: string): Promise<Blob> {
  const response = await fetch("/v1/audio/speech", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ input: text }),
  })

  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || `Speech synthesis failed (${response.status})`)
  }

  return response.blob()
}
