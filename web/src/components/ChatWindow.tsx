import { useEffect, useRef } from "react"
import { AlertTriangle, Code2, FileSearch, Sparkles } from "lucide-react"
import { MessageBubble } from "./MessageBubble"
import type { DisplayMessage } from "../lib/types"

const SUGGESTIONS = [
  { icon: Code2, text: "Write a Python function to reverse a linked list" },
  { icon: FileSearch, text: "Summarize the attached document in 3 bullet points" },
  { icon: Sparkles, text: "Explain the CAP theorem like I'm new to distributed systems" },
]

export function ChatWindow({
  messages,
  error,
  onSuggestion,
}: {
  messages: DisplayMessage[]
  error: string | null
  onSuggestion: (text: string) => void
}) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  if (messages.length === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-6 px-6 text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-600 to-fuchsia-600 text-2xl font-bold text-white shadow-lg">
          L
        </div>
        <div>
          <h2 className="text-xl font-semibold text-zinc-800 dark:text-zinc-100">
            What can LAIR route for you today?
          </h2>
          <p className="mt-1 text-sm text-zinc-400">
            Every request is auto-matched to the best local model running on your machine.
          </p>
        </div>

        <div className="grid w-full max-w-xl gap-2 sm:grid-cols-1">
          {SUGGESTIONS.map(({ icon: Icon, text }) => (
            <button
              key={text}
              onClick={() => onSuggestion(text)}
              className="flex items-center gap-3 rounded-2xl border border-white/30 bg-white/40 px-4 py-3 text-left text-sm text-zinc-600 backdrop-blur-xl transition hover:border-violet-300/60 hover:bg-violet-500/10 dark:border-white/10 dark:bg-white/5 dark:text-zinc-300 dark:hover:border-violet-500/40"
            >
              <Icon size={16} className="shrink-0 text-violet-500" />
              {text}
            </button>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      <div className="mx-auto flex max-w-3xl flex-col gap-5">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}

        {error && (
          <div className="flex items-center gap-2 rounded-xl border border-rose-300/50 bg-rose-50/60 px-4 py-3 text-sm text-rose-600 backdrop-blur-xl dark:border-rose-900/50 dark:bg-rose-950/30 dark:text-rose-300">
            <AlertTriangle size={16} className="shrink-0" />
            {error}
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  )
}
