import { MessageSquarePlus, Trash2 } from "lucide-react"
import type { StoredConversation } from "../lib/conversationStore"

interface SidebarProps {
  conversations: StoredConversation[]
  activeId: string
  onSelect: (id: string) => void
  onCreate: () => void
  onDelete: (id: string) => void
}

export function Sidebar({ conversations, activeId, onSelect, onCreate, onDelete }: SidebarProps) {
  const sorted = [...conversations].sort((a, b) => b.updatedAt - a.updatedAt)

  return (
    <aside className="flex w-64 shrink-0 flex-col gap-3 border-r border-white/20 bg-white/40 p-3 backdrop-blur-xl dark:border-white/10 dark:bg-white/5">
      <button
        type="button"
        onClick={onCreate}
        className="flex items-center gap-2 rounded-xl border border-white/30 bg-white/60 px-3 py-2.5 text-sm font-medium text-zinc-700 shadow-sm backdrop-blur transition hover:bg-white/80 dark:border-white/10 dark:bg-white/10 dark:text-zinc-100 dark:hover:bg-white/15"
      >
        <MessageSquarePlus size={16} className="text-violet-500" />
        New chat
      </button>

      <div className="flex flex-1 flex-col gap-1 overflow-y-auto">
        {sorted.map((conversation) => (
          <button
            key={conversation.id}
            onClick={() => onSelect(conversation.id)}
            className={`group flex items-center gap-2 rounded-xl px-3 py-2 text-left text-sm transition ${
              conversation.id === activeId
                ? "bg-gradient-to-r from-violet-500/20 to-fuchsia-500/20 text-violet-700 dark:text-violet-200"
                : "text-zinc-600 hover:bg-white/50 dark:text-zinc-300 dark:hover:bg-white/10"
            }`}
          >
            <span className="flex-1 truncate">{conversation.title}</span>
            <span
              role="button"
              tabIndex={0}
              onClick={(e) => {
                e.stopPropagation()
                onDelete(conversation.id)
              }}
              className="shrink-0 text-zinc-400 opacity-0 transition hover:text-rose-500 group-hover:opacity-100"
            >
              <Trash2 size={13} />
            </span>
          </button>
        ))}
      </div>

      <p className="px-1 text-[10px] leading-relaxed text-zinc-400">
        Conversations are stored only in this browser -- LAIR itself keeps no chat history.
      </p>
    </aside>
  )
}
