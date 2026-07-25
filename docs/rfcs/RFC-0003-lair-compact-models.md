# RFC-0003 — LAIR Compact Models (Quantum-Inspired Tensor-Network Compression)

**Status:** Accepted (Phase 1a)

**Date:** 2026-07-25

---

## Summary

I-19's long-term goal: a community library of tensor-network-compressed ("quantum-inspired," per CompactifAI/arXiv 2401.14109) open models, small enough to run well on machines that can't run the originals, published as ordinary GGUF/safetensors artifacts anyone can run on a plain CPU. This RFC covers **Phase 1a only** -- reproducing the core matrix-product-operator (MPO) decomposition math and validating it mechanically, per the plan's own "Phase 1 (research)... RFC first" sequencing. Phases 1b (a real small open model), 2 (catalog), and 3 (community contributions) are named, scoped, and explicitly not started.

---

## Motivation

Per `docs/INNOVATION_PLAN_2026.md` §1.10, tensor-network (MPO) compression achieves up to ~93-95% size reduction with ~90%+ accuracy retention on real trained LLMs, and the compressed models run on plain CPUs -- Multiverse monetizes this via cloud; LAIR's differentiated angle is bringing it to local machines, free. Before committing to that roadmap, Phase 1's job is to confirm the technique is actually reproducible with open tooling (`tensorly`, not a proprietary pipeline) and to characterize its real behavior, including where it doesn't work as naively expected.

---

## Background

Nothing in this codebase does tensor decomposition today. `tensorly` (numpy-backed, no torch -- `pip install tensorly` pulls in only `numpy`/`scipy`, consistent with this project's own accessibility-driven dependency choices already made for `fastembed` over `sentence-transformers`, I-08/ADR-0019) provides `tensor_train_matrix`, a direct implementation of the tensor-train-matrix decomposition that MPO compression is built on.

---

## What Phase 1a Actually Did

`scripts/compactify/pipeline.py` (real, tested, runnable via `python -m scripts.compactify.run_demo`):

- Constructs a synthetic matrix with a **known, exact ordinary rank** (via `A @ B` for skinny `A`/`B`) -- a stand-in for the kind of learned redundancy real trained weight matrices have.
- Compresses it via `tensor_train_matrix` at several internal ranks, measuring parameter-count reduction and relative reconstruction error (Frobenius norm).
- Compares against an **incompressible random matrix of identical shape** as a baseline.
- Includes a **sanity check**: at maximal TT-rank, reconstruction is near-exact (`~3e-7` relative error), confirming the decomposition/reconstruction implementation itself is correct.

### The honest finding

The constructed low-rank matrix (true ordinary rank 4, out of 256) did **not** compress meaningfully better than the incompressible random baseline at low TT-ranks, once reshaped into a 4D tensor for `tensor_train_matrix`. This is a real, reproducible result, not a bug -- confirmed by checking `np.linalg.matrix_rank` on the un-reshaped matrix (genuinely 4) alongside the max-rank sanity check (confirming the decomposition math is correct). **The reshape/tensorization choice determines whether a matrix's actual low-rank structure is exposed as a low TT-rank** -- an arbitrary reshape does not automatically preserve ordinary-rank structure across the tensor-train factorization. This matches what the tensor-network compression literature emphasizes and CompactifAI's own reported results depend on: real applications to transformer weights use tensorization schemes deliberately aligned with the model's actual structure (attention heads, hidden-dimension groupings), not an arbitrary reshape.

---

## Decision

- **Ship Phase 1a as-is**: a real, working, tested compression/reconstruction pipeline on synthetic matrices, with the tensorization-sensitivity finding documented prominently (not hidden as a failure) -- this is exactly the kind of result Phase 1 research is supposed to surface before further investment.
- **`configs/compact_models/catalog.json`** ships empty, mirroring I-12's `community_scores.json` pattern (`app/registry/compact_models.py`'s `CompactModelCatalogLoader`) -- the format and loader exist now so Phase 2 has somewhere to write to, but no entry is fabricated ahead of a real compressed-and-benchmarked model existing.
- **Quality bar for any future real entry**: retained benchmark score >= 90% of the source model's own measured score (per the plan's own acceptance criterion), `provenance=MEASURED` always -- this catalog exists specifically to carry real numbers, never a guess.
- **Framing discipline, stated explicitly**: "quantum-inspired" means tensor networks (mathematical structures also used in quantum computing) run entirely on classical hardware (a plain CPU) -- nothing here touches, simulates, or requires actual quantum hardware. Real-QPU work (IBM Cayley adapters, per the plan's own watch-list) stays a watch-list item only, never conflated with this.

---

## Alternatives Considered

### Skip straight to compressing a real small open model (e.g. SmolLM3-3B)

Cons

- Requires downloading a multi-hundred-MB-to-multi-GB model, a `transformers`/model-loading dependency this pass doesn't need yet, and -- per the plan's own text -- a real GPU-time "healing" retrain step to recover quality after compression, none of which this pass has the resources to do responsibly. Validating the underlying math first, cheaply and reproducibly, is the correct research order -- and it surfaced a real finding (tensorization sensitivity) that will matter directly when Phase 1b does use a real model's weights.

### Use `quimb` (named in the plan) instead of `tensorly`

Cons

- `quimb` is oriented toward general tensor-network / quantum-circuit simulation; `tensorly`'s `tensor_train_matrix` is a more direct, purpose-built implementation of the specific TT-matrix decomposition MPO compression relies on, with a lighter dependency footprint (numpy/scipy only). `quimb` remains worth revisiting if Phase 1b's needs (e.g. more general tensor-network contraction) outgrow `tensorly`.

### Hide or soften the tensorization-sensitivity finding

Cons

- Directly contradicts this project's evidence-over-optimism discipline (ADR-0011, ADR-0015's dogfooding philosophy) -- a Phase 1 research pass that only reports favorable numbers isn't research, and the next person to pick up I-19 needs this finding to design Phase 1b's tensorization correctly.

---

## Consequences

Benefits

- A real, reproducible, tested compression pipeline exists and is importable (`scripts/compactify/pipeline.py`), not just a demo script
- A genuine research finding (tensorization choice matters) that directly informs Phase 1b's design, rather than a superficial "it worked" result that would mislead that work
- Catalog format + loader ready for Phase 2, with zero fabricated entries

Trade-offs

- Phase 1a does not compress a real model -- I-19's own acceptance criterion ("one reproducible compression of a small open model with before/after benchmarks") is **not yet met**; Phase 1b is concretely named, not silently dropped
- No quality-retention percentage exists yet for anything in the catalog (it's empty) -- "Compact-model catalog format + loader" is satisfied structurally, not populated
- `tensorly`/`scipy` are new dependencies (test-only, per `requirements.txt`'s own comment) -- add real weight to the install for anyone running the full test suite, though not to LAIR's actual running server

---

## Dependencies

- `tensorly` (+ its own `scipy` dependency) -- added to `requirements.txt` marked test-only (mirroring `reportlab`'s existing precedent there), since `scripts/compactify` and its tests are the only consumers; nothing in LAIR's running server imports it
- A new ADR is **not** required for Phase 1a (no schema/architecture decision beyond what this RFC already covers); Phase 1b will likely need one for the catalog's real-entry schema once populated

---

## Success Criteria (Phase 1a)

- Decomposition/reconstruction pipeline is real and passes a max-rank sanity check (near-zero reconstruction error)
- The compressibility-vs-tensorization relationship is characterized with an honest, reproducible finding, not asserted without evidence
- Catalog loader works against both an empty and a populated catalog file

---

## Future Work (Phase 1b, 2, 3)

- **Phase 1b**: apply the validated pipeline to a real small open model's real weights (e.g. SmolLM3 or a small Qwen variant), with a tensorization scheme chosen to match the model's actual structure (informed directly by this RFC's finding) -- and be honest about whether a healing retrain step is in scope without real GPU time.
- **Phase 2**: populate `configs/compact_models/catalog.json` with vetted, MEASURED entries once Phase 1b produces real before/after benchmark scores.
- **Phase 3**: accept community-contributed compressions with mandatory benchmark cards, provenance-tagged, mirroring I-12's community-contribution model.
