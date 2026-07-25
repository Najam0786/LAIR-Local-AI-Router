import { Mic, Square, Loader2 } from "lucide-react"
import { useState } from "react"
import { useVoiceRecorder } from "../hooks/useVoiceRecorder"
import { transcribeAudio } from "../lib/api"

export function VoiceButton({ onResult }: { onResult: (text: string) => void }) {
  const { isRecording, start, stop } = useVoiceRecorder()
  const [busy, setBusy] = useState(false)

  const handleClick = async () => {
    if (!isRecording) {
      await start()
      return
    }

    setBusy(true)
    try {
      const blob = await stop()
      const result = await transcribeAudio(blob)
      if (result.text) onResult(result.text)
    } catch {
      // Voice extras may not be installed; the composer's text input
      // remains fully usable either way.
    } finally {
      setBusy(false)
    }
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={busy}
      title={isRecording ? "Stop recording" : "Speak your message"}
      className={`flex h-10 w-10 items-center justify-center rounded-full transition ${
        isRecording
          ? "mic-recording bg-rose-500 text-white"
          : "bg-zinc-100 text-zinc-500 hover:bg-zinc-200 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-700"
      }`}
    >
      {busy ? (
        <Loader2 size={18} className="animate-spin" />
      ) : isRecording ? (
        <Square size={16} />
      ) : (
        <Mic size={18} />
      )}
    </button>
  )
}
