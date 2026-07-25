import { Cpu, Cloud } from "lucide-react"
import type { LairMeta } from "../lib/types"

export function ModelBadge({ modelId, meta }: { modelId: string | null; meta?: LairMeta | null }) {
  if (!modelId) return null

  const cloud = meta?.routed_to_cloud

  return (
    <div
      className={`flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium ${
        cloud
          ? "border-amber-400/40 bg-amber-400/10 text-amber-600 dark:text-amber-300"
          : "border-violet-400/40 bg-violet-400/10 text-violet-600 dark:text-violet-300"
      }`}
      title={cloud ? meta?.cloud_escalation_reason ?? "Cloud escalation" : "Auto-routed by LAIR"}
    >
      {cloud ? <Cloud size={13} /> : <Cpu size={13} />}
      <span className="max-w-[16rem] truncate">{modelId}</span>
      {meta?.cache_hit && (
        <span className="rounded-full bg-emerald-400/20 px-1.5 py-0.5 text-[10px] text-emerald-600 dark:text-emerald-300">
          cached
        </span>
      )}
    </div>
  )
}
