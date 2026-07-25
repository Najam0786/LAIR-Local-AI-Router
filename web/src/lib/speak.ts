import { synthesizeSpeech } from "./api"

/** Shared by the manual "Listen" button and voice-mode auto-playback. */
export async function speak(text: string): Promise<void> {
  if (!text) return

  const blob = await synthesizeSpeech(text)
  const url = URL.createObjectURL(blob)
  const audio = new Audio(url)
  audio.onended = () => URL.revokeObjectURL(url)
  await audio.play()
}
