interface SwitchProps {
  label: string
  checked: boolean
  onChange: (checked: boolean) => void
  icon?: React.ReactNode
}

export function Switch({ label, checked, onChange, icon }: SwitchProps) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className="flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-medium text-zinc-600 transition hover:bg-zinc-200/60 dark:text-zinc-300 dark:hover:bg-white/10"
    >
      {icon}
      <span>{label}</span>
      <span
        className={`relative h-5 w-9 rounded-full transition-colors ${
          checked
            ? "bg-gradient-to-r from-violet-500 to-fuchsia-500"
            : "bg-zinc-300 dark:bg-zinc-700"
        }`}
      >
        <span
          className={`absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-transform ${
            checked ? "translate-x-4" : "translate-x-0.5"
          }`}
        />
      </span>
    </button>
  )
}
