import { useState } from "react"
import { Activity, ChevronDown, Gauge, Globe2, Radar } from "lucide-react"
import type { RoutingPlan, ScoredCandidate } from "../lib/routing"
import type { Provenance } from "../lib/types"

const PROVENANCE_STYLE: Record<Provenance, string> = {
  measured: "bg-emerald-400/15 text-emerald-600 dark:text-emerald-300",
  community: "bg-sky-400/15 text-sky-600 dark:text-sky-300",
  declared: "bg-zinc-400/15 text-zinc-600 dark:text-zinc-300",
  heuristic: "bg-amber-400/15 text-amber-600 dark:text-amber-300",
  memory: "bg-violet-400/15 text-violet-600 dark:text-violet-300",
}

function CandidateCard({
  candidate,
  isSelected,
  defaultOpen,
}: {
  candidate: ScoredCandidate
  isSelected: boolean
  defaultOpen: boolean
}) {
  const [open, setOpen] = useState(defaultOpen)

  return (
    <div
      className={`overflow-hidden rounded-xl border backdrop-blur transition ${
        isSelected
          ? "border-violet-400/50 bg-violet-400/10"
          : "border-white/20 bg-white/40 dark:border-white/10 dark:bg-white/5"
      }`}
    >
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-2 px-3 py-2 text-left"
      >
        {isSelected && <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-violet-500" />}
        <span className="flex-1 truncate text-xs font-medium text-zinc-700 dark:text-zinc-200">
          {candidate.model.id}
        </span>
        <span className="text-[11px] font-semibold text-zinc-500">
          {candidate.breakdown.total_score.toFixed(2)}
        </span>
        <ChevronDown
          size={13}
          className={`shrink-0 text-zinc-400 transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>

      {open && (
        <ul className="space-y-1.5 border-t border-white/10 px-3 py-2">
          {candidate.breakdown.factors.map((factor, i) => (
            <li key={i} className="flex items-start justify-between gap-2 text-[11px]">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1.5">
                  <span className="font-medium text-zinc-600 dark:text-zinc-300">{factor.name}</span>
                  <span
                    className={`shrink-0 rounded-full px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-wide ${PROVENANCE_STYLE[factor.provenance]}`}
                  >
                    {factor.provenance}
                  </span>
                </div>
                <p className="mt-0.5 text-zinc-400">{factor.reason}</p>
              </div>
              <span className="shrink-0 font-mono text-zinc-500">{factor.score.toFixed(2)}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export function SystemPanel({ plan, isThinking }: { plan: RoutingPlan | null; isThinking: boolean }) {
  const decision = plan?.decision

  return (
    <aside className="flex w-80 shrink-0 flex-col gap-3 overflow-y-auto border-l border-white/20 bg-white/40 p-4 backdrop-blur-xl dark:border-white/10 dark:bg-white/5">
      <div className="flex items-center gap-2 text-sm font-semibold text-zinc-700 dark:text-zinc-200">
        <Radar size={16} className="text-violet-500" />
        Routing
      </div>

      {!decision && (
        <p className="text-xs text-zinc-400">
          {isThinking ? "Scoring candidate models..." : "Send a message to see how LAIR routes it."}
        </p>
      )}

      {decision && (
        <>
          <div className="rounded-xl border border-white/20 bg-white/50 p-3 backdrop-blur dark:border-white/10 dark:bg-white/5">
            <p className="truncate text-xs font-semibold text-violet-600 dark:text-violet-300">
              {decision.selected_model.id}
            </p>

            <div className="mt-2 flex items-center gap-1.5 text-[11px] text-zinc-500">
              <Gauge size={12} />
              Confidence
              <span className="ml-auto font-mono text-zinc-600 dark:text-zinc-300">
                {Math.round(decision.confidence * 100)}%
              </span>
            </div>
            <div className="mt-1 h-1.5 w-full rounded-full bg-zinc-200/60 dark:bg-zinc-700/60">
              <div
                className={`h-1.5 rounded-full bg-gradient-to-r ${
                  decision.confidence >= 0.6
                    ? "from-emerald-500 to-teal-400"
                    : decision.confidence >= 0.3
                      ? "from-amber-500 to-orange-400"
                      : "from-rose-500 to-fuchsia-500"
                }`}
                style={{ width: `${Math.round(decision.confidence * 100)}%` }}
              />
            </div>

            <div className="mt-3 flex flex-wrap gap-1.5 text-[11px] text-zinc-500">
              {decision.complexity && (
                <span className="flex items-center gap-1 rounded-full bg-zinc-400/10 px-2 py-0.5">
                  <Activity size={11} /> complexity {decision.complexity.level}/5
                </span>
              )}
              {decision.language_code && (
                <span className="flex items-center gap-1 rounded-full bg-zinc-400/10 px-2 py-0.5">
                  <Globe2 size={11} /> {decision.language_code}
                </span>
              )}
            </div>

            {decision.reasons.length > 0 && (
              <ul className="mt-3 space-y-1 text-[11px] text-zinc-500">
                {decision.reasons.map((reason, i) => (
                  <li key={i}>- {reason}</li>
                ))}
              </ul>
            )}
          </div>

          <p className="px-0.5 text-[10px] font-medium uppercase tracking-wide text-zinc-400">
            Candidates
          </p>

          <div className="flex flex-col gap-2">
            {decision.candidates.map((candidate) => (
              <CandidateCard
                key={candidate.model.id}
                candidate={candidate}
                isSelected={candidate.model.id === decision.selected_model.id}
                defaultOpen={candidate.model.id === decision.selected_model.id}
              />
            ))}
          </div>
        </>
      )}
    </aside>
  )
}
