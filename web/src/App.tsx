import { useState } from "react"
import { useConversations } from "./hooks/useConversations"
import { useTheme } from "./hooks/useTheme"
import { Header } from "./components/Header"
import { Sidebar } from "./components/Sidebar"
import { SystemPanel } from "./components/SystemPanel"
import { ChatWindow } from "./components/ChatWindow"
import { Composer } from "./components/Composer"

export default function App() {
  const { theme, toggle } = useTheme()
  const {
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
  } = useConversations()
  const [noCache, setNoCache] = useState(false)
  const [documentId, setDocumentId] = useState<string | null>(null)
  const [projectScope, setProjectScope] = useState<string | null>(null)
  const [savingsRefreshKey, setSavingsRefreshKey] = useState(0)

  const handleSend = (text: string, opts?: { viaVoice?: boolean }) => {
    send(text, { noCache, documentId, projectScope, viaVoice: opts?.viaVoice }).then(() =>
      setSavingsRefreshKey((k) => k + 1),
    )
  }

  return (
    <div className="flex h-screen flex-col text-zinc-900 dark:text-zinc-100">
      <div className="glass-backdrop">
        <div className="glass-backdrop-accent" />
      </div>

      <Header
        theme={theme}
        onToggleTheme={toggle}
        noCache={noCache}
        onToggleNoCache={setNoCache}
        projectScope={projectScope}
        onChangeProjectScope={setProjectScope}
        savingsRefreshKey={savingsRefreshKey}
      />

      <div className="flex min-h-0 flex-1">
        <Sidebar
          conversations={conversations}
          activeId={activeId}
          onSelect={selectConversation}
          onCreate={createConversation}
          onDelete={deleteConversation}
        />

        <div className="flex min-w-0 flex-1 flex-col">
          <ChatWindow messages={messages} error={error} onSuggestion={handleSend} />

          <Composer
            onSend={handleSend}
            onStop={stop}
            isStreaming={isStreaming}
            documentId={documentId}
            onSelectDocument={setDocumentId}
          />
        </div>

        <SystemPanel plan={routingPlan} isThinking={isStreaming} />
      </div>
    </div>
  )
}
