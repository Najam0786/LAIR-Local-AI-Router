import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { Volume2, Loader2, Mic } from "lucide-react"
import { useState } from "react"
import { speak as speakText } from "../lib/speak"
import type { DisplayMessage } from "../lib/types"
import { ModelBadge } from "./ModelBadge"

export function MessageBubble({ message }: { message: DisplayMessage }) {
  const isUser = message.role === "user"
  const [speaking, setSpeaking] = useState(false)

  const speak = async () => {
    if (speaking || !message.content) return
    setSpeaking(true)

    try {
      await speakText(message.content)
    } catch {
      // Voice extras may not be installed -- fail silently, this is a
      // convenience affordance, not a core chat capability.
    } finally {
      setSpeaking(false)
    }
  }

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`flex max-w-[85%] flex-col gap-1.5 ${isUser ? "items-end" : "items-start"}`}>
        {!isUser && message.meta?.model_used && (
          <ModelBadge modelId={message.meta.model_used} meta={message.meta} />
        )}

        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-lg backdrop-blur-xl ${
            isUser
              ? "rounded-tr-sm bg-gradient-to-br from-violet-600/90 to-fuchsia-600/90 text-white"
              : "rounded-tl-sm border border-white/30 bg-white/50 text-zinc-800 dark:border-white/10 dark:bg-white/10 dark:text-zinc-100"
          }`}
        >
          {isUser && message.viaVoice && (
            <span className="mb-1 flex items-center gap-1 text-[11px] text-white/70">
              <Mic size={10} /> via voice
            </span>
          )}

          {message.content ? (
            <div
              className={`prose prose-sm max-w-none prose-pre:bg-zinc-900/90 prose-pre:text-zinc-100 ${
                isUser ? "prose-invert" : "dark:prose-invert"
              }`}
            >
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
            </div>
          ) : (
            <span className="typing-caret text-zinc-400">&nbsp;</span>
          )}
        </div>

        {!isUser && message.content && !message.streaming && (
          <button
            type="button"
            onClick={speak}
            className="flex items-center gap-1 text-xs text-zinc-400 transition hover:text-violet-500"
            title="Read this reply aloud"
          >
            {speaking ? <Loader2 size={12} className="animate-spin" /> : <Volume2 size={12} />}
            Listen
          </button>
        )}
      </div>
    </div>
  )
}
