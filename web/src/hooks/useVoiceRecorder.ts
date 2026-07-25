import { useCallback, useRef, useState } from "react"

/**
 * Wraps MediaRecorder for a press-to-toggle mic button. Kept dependency-free
 * (no external recorder lib) since MediaRecorder + webm/opus is supported by
 * every browser LAIR's target users run.
 */
export function useVoiceRecorder() {
  const [isRecording, setIsRecording] = useState(false)
  const recorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const streamRef = useRef<MediaStream | null>(null)

  const start = useCallback(async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    streamRef.current = stream
    chunksRef.current = []

    const recorder = new MediaRecorder(stream)
    recorder.ondataavailable = (event) => {
      if (event.data.size > 0) chunksRef.current.push(event.data)
    }
    recorder.start()
    recorderRef.current = recorder
    setIsRecording(true)
  }, [])

  const stop = useCallback((): Promise<Blob> => {
    return new Promise((resolve) => {
      const recorder = recorderRef.current

      if (!recorder) {
        resolve(new Blob())
        return
      }

      recorder.onstop = () => {
        streamRef.current?.getTracks().forEach((track) => track.stop())
        setIsRecording(false)
        resolve(new Blob(chunksRef.current, { type: "audio/webm" }))
      }
      recorder.stop()
    })
  }, [])

  return { isRecording, start, stop }
}
