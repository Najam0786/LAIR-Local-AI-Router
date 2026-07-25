import { useCallback, useEffect, useRef, useState } from "react"
import { streamChat } from "../lib/api"
import { speak } from "../lib/speak"
import { explainRouting, type RoutingPlan } from "../lib/routing"
import {
  loadConversations,
  saveConversations,
  titleFor,
  type StoredConversation,
} from "../lib/conversationStore"
import type { DisplayMessage } from "../lib/types"

export interface SendOptions {
  noCache: boolean
  documentId: string | null
  projectScope: string | null
  viaVoice?: boolean
}

let nextId = 0
const newId = (prefix: string) => `${prefix}${Date.now()}-${nextId++}`

function newConversation(): StoredConversation {
  return { id: newId("c"), title: "New chat", messages: [], updatedAt: Date.now() }
}

export function useConversations() {
  const [conversations, setConversations] = useState<StoredConversation[]>(() => {
    const stored = loadConversations()
    return stored.length > 0 ? stored : [newConversation()]
  })
  const [activeId, setActiveId] = useState<string>(() => conversations[0].id)
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [routingPlan, setRoutingPlan] = useState<RoutingPlan | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    saveConversations(conversations)
  }, [conversations])

  const active = conversations.find((c) => c.id === activeId) ?? conversations[0]
  const messages = active.messages

  const patchActive = useCallback(
    (updater: (msgs: DisplayMessage[]) => DisplayMessage[]) => {
      setConversations((prev) =>
        prev.map((c) => {
          if (c.id !== activeId) return c
          const nextMessages = updater(c.messages)
          return { ...c, messages: nextMessages, updatedAt: Date.now(), title: titleFor(nextMessages) }
        }),
      )
    },
    [activeId],
  )

  const send = useCallback(
    async (prompt: string, options: SendOptions) => {
      setError(null)
      setRoutingPlan(null)
      const userMessage: DisplayMessage = {
        id: newId("m"),
        role: "user",
        content: prompt,
        viaVoice: options.viaVoice,
      }
      const assistantId = newId("m")
      let fullContent = ""

      patchActive((prev) => [
        ...prev,
        userMessage,
        { id: assistantId, role: "assistant", content: "", streaming: true },
      ])
      setIsStreaming(true)
      explainRouting(prompt).then(setRoutingPlan)

      const controller = new AbortController()
      abortRef.current = controller

      try {
        const wireMessages = [...messages, userMessage].map((m) => ({
          role: m.role,
          content: m.content,
        }))

        for await (const delta of streamChat(wireMessages, {
          noCache: options.noCache,
          documentId: options.documentId,
          projectScope: options.projectScope,
          signal: controller.signal,
        })) {
          if (delta.done) break

          fullContent += delta.content
          patchActive((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, content: m.content + delta.content, meta: delta.meta ?? m.meta }
                : m,
            ),
          )
        }
      } catch (err) {
        if ((err as Error).name !== "AbortError") {
          setError((err as Error).message)
        }
      } finally {
        patchActive((prev) =>
          prev.map((m) => (m.id === assistantId ? { ...m, streaming: false } : m)),
        )
        setIsStreaming(false)
        abortRef.current = null

        if (options.viaVoice && fullContent) {
          speak(fullContent).catch(() => {})
        }
      }
    },
    [messages, patchActive],
  )

  const stop = useCallback(() => {
    abortRef.current?.abort()
  }, [])

  const createConversation = useCallback(() => {
    const fresh = newConversation()
    setConversations((prev) => [fresh, ...prev])
    setActiveId(fresh.id)
    setRoutingPlan(null)
  }, [])

  const selectConversation = useCallback((id: string) => {
    setActiveId(id)
    setRoutingPlan(null)
  }, [])

  const deleteConversation = useCallback(
    (id: string) => {
      const remaining = conversations.filter((c) => c.id !== id)
      const finalList = remaining.length > 0 ? remaining : [newConversation()]
      setConversations(finalList)
      if (activeId === id) setActiveId(finalList[0].id)
    },
    [conversations, activeId],
  )

  return {
    conversations,
    activeId,
    messages,
    send,
    stop,
    isStreaming,
    error,
    routingPlan,
    createConversation,
    selectConversation,
    deleteConversation,
  }
}
