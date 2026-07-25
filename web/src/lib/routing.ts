import type { Provenance } from "./types"

export interface ScoreFactor {
  name: string
  score: number
  provenance: Provenance
  reason: string
}

export interface ScoreBreakdown {
  total_score: number
  capability_score: number
  streaming_score: number
  context_window_score: number
  benchmark_score: number
  loaded_bonus_score: number
  complexity_score: number
  quant_efficiency_score: number
  language_score: number
  battery_score: number
  matched_capabilities: string[]
  factors: ScoreFactor[]
}

export interface ScoredCandidate {
  model: { id: string }
  breakdown: ScoreBreakdown
}

export interface DecisionRecord {
  candidates: ScoredCandidate[]
  selected_model: { id: string }
  confidence: number
  reasons: string[]
  complexity: { level: number; reasons: string[] } | null
  language_code: string | null
}

export interface RoutingPlan {
  decision: DecisionRecord
}

/**
 * Fetches a routing explanation for `prompt` via the dry-run POST /route
 * endpoint (no inference happens) -- powers the live system panel. Runs
 * in parallel with the real streamed chat request, not instead of it;
 * a failure here should never block the actual reply.
 */
export async function explainRouting(prompt: string): Promise<RoutingPlan | null> {
  try {
    const response = await fetch("/route", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    })

    if (!response.ok) return null

    const body = await response.json()
    return body.plan as RoutingPlan
  } catch {
    return null
  }
}
