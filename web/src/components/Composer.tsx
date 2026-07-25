import { useRef, useState } from "react"
import { ArrowUp, Square } from "lucide-react"
import { VoiceButton } from "./VoiceButton"
import { DocumentPanel } from "./DocumentPanel"

interface ComposerProps {
  onSend: (text: string, opts?: { viaVoice?: boolean }) => void
  onStop: () => void
  isStreaming: boolean
  documentId: string | null
  onSelectDocument: (id: string | null) => void
}

export function Composer({
  onSend,
  onStop,
  isStreaming,
  documentId,
  onSelectDocument,
}: ComposerProps) {
  const [value, setValue] = useState("")
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const submit = () => {
    const trimmed = value.trim()
    if (!trimmed || isStreaming) return
    onSend(trimmed)
    setValue("")
    if (textareaRef.current) textareaRef.current.style.height = "auto"
  }

  return (
    <div className="border-t border-white/20 bg-white/40 p-4 backdrop-blur-xl dark:border-white/10 dark:bg-white/5">
      <div className="mx-auto flex max-w-3xl items-end gap-2">
        <DocumentPanel activeDocumentId={documentId} onSelect={onSelectDocument} />

        <div className="flex flex-1 items-end rounded-3xl border border-white/30 bg-white/50 px-4 py-2 backdrop-blur transition focus-within:border-violet-400/60 dark:border-white/10 dark:bg-white/10">
          <textarea
            ref={textareaRef}
            value={value}
            rows={1}
            placeholder={documentId ? "Ask about the attached document..." : "Message LAIR..."}
            onChange={(e) => {
              setValue(e.target.value)
              e.target.style.height = "auto"
              e.target.style.height = `${Math.min(e.target.scrollHeight, 160)}px`
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault()
                submit()
              }
            }}
            className="max-h-40 w-full resize-none bg-transparent text-sm text-zinc-800 outline-none placeholder:text-zinc-400 dark:text-zinc-100"
          />
        </div>

        <VoiceButton onResult={(text) => onSend(text, { viaVoice: true })} />

        <button
          type="button"
          onClick={isStreaming ? onStop : submit}
          disabled={!isStreaming && !value.trim()}
          title={isStreaming ? "Stop generating" : "Send"}
          className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-violet-600 to-fuchsia-600 text-white shadow-md transition disabled:cursor-not-allowed disabled:opacity-30"
        >
          {isStreaming ? <Square size={16} /> : <ArrowUp size={18} />}
        </button>
      </div>

      {documentId && (
        <p className="mx-auto mt-1.5 max-w-3xl text-center text-[11px] text-zinc-400">
          Answers will draw on the attached document.
        </p>
      )}
    </div>
  )
}
