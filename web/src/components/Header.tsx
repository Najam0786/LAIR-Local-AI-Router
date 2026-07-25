import { Database, Moon, ShieldOff, Sun } from "lucide-react"
import { Switch } from "./Switch"
import { SavingsBadge } from "./SavingsBadge"

interface HeaderProps {
  theme: "dark" | "light"
  onToggleTheme: () => void
  noCache: boolean
  onToggleNoCache: (checked: boolean) => void
  projectScope: string | null
  onChangeProjectScope: (scope: string | null) => void
  savingsRefreshKey: number
}

export function Header({
  theme,
  onToggleTheme,
  noCache,
  onToggleNoCache,
  projectScope,
  onChangeProjectScope,
  savingsRefreshKey,
}: HeaderProps) {
  return (
    <header className="flex items-center justify-between border-b border-white/20 bg-white/40 px-5 py-3 backdrop-blur-xl dark:border-white/10 dark:bg-white/5">
      <div className="flex items-center gap-2.5">
        <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-violet-600 to-fuchsia-600 text-sm font-bold text-white shadow-md">
          L
        </div>
        <div>
          <h1 className="text-sm font-semibold text-zinc-800 dark:text-zinc-100">LAIR</h1>
          <p className="text-[11px] text-zinc-400">Local AI Intelligence Router</p>
        </div>
      </div>

      <div className="flex items-center gap-1.5">
        <SavingsBadge refreshKey={savingsRefreshKey} />

        <Switch
          label="Memory"
          icon={<Database size={13} />}
          checked={!!projectScope}
          onChange={(checked) => onChangeProjectScope(checked ? "default" : null)}
        />

        <Switch
          label="No cache"
          icon={<ShieldOff size={13} />}
          checked={noCache}
          onChange={onToggleNoCache}
        />

        <button
          type="button"
          onClick={onToggleTheme}
          title="Toggle theme"
          className="flex h-8 w-8 items-center justify-center rounded-full text-zinc-500 transition hover:bg-zinc-200/60 dark:text-zinc-300 dark:hover:bg-white/10"
        >
          {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
        </button>
      </div>
    </header>
  )
}
