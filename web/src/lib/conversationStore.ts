import type { DisplayMessage } from "./types"

export interface StoredConversation {
  id: string
  title: string
  messages: DisplayMessage[]
  updatedAt: number
}

const STORAGE_KEY = "lair.conversations"

/**
 * Chat history has nowhere to live server-side -- /v1/chat/completions
 * is intentionally stateless (see Conversation's docstring in
 * app/execution/conversation.py). The sidebar's conversation list is
 * purely a browser-local convenience, not a LAIR feature; clearing
 * browser storage loses it with no server-side trace to recover.
 */
export function loadConversations(): StoredConversation[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    return JSON.parse(raw) as StoredConversation[]
  } catch {
    return []
  }
}

export function saveConversations(conversations: StoredConversation[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations))
  } catch {
    // Storage full or unavailable (private browsing) -- the session
    // still works, it just won't survive a reload.
  }
}

export function titleFor(messages: DisplayMessage[]): string {
  const firstUser = messages.find((m) => m.role === "user")
  if (!firstUser) return "New chat"
  const trimmed = firstUser.content.trim().replace(/\s+/g, " ")
  return trimmed.length > 48 ? `${trimmed.slice(0, 48)}...` : trimmed || "New chat"
}
