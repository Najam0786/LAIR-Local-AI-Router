import { useEffect, useState } from "react"
import { PiggyBank } from "lucide-react"
import { getSavings } from "../lib/api"

export function SavingsBadge({ refreshKey }: { refreshKey: number }) {
  const [dayUsd, setDayUsd] = useState<number | null>(null)

  useEffect(() => {
    let cancelled = false

    getSavings()
      .then((res) => {
        if (!cancelled) setDayUsd(res.day_usd)
      })
      .catch(() => {
        if (!cancelled) setDayUsd(null)
      })

    return () => {
      cancelled = true
    }
  }, [refreshKey])

  if (dayUsd === null) return null

  return (
    <div
      className="flex items-center gap-1.5 rounded-full border border-emerald-400/40 bg-emerald-400/10 px-3 py-1 text-xs font-medium text-emerald-600 dark:text-emerald-300"
      title="Estimated cloud-equivalent cost avoided today by routing locally"
    >
      <PiggyBank size={13} />
      <span>${dayUsd.toFixed(3)} saved today</span>
    </div>
  )
}
