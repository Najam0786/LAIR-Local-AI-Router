"""
Runnable Phase 1a demo (I-19): prints the compression pipeline's
findings on synthetic weight-shaped matrices. See pipeline.py's module
docstring for what this does and does not prove.

Usage: python -m scripts.compactify.run_demo
"""

from scripts.compactify.pipeline import run_phase1a_demo


def _print_results(label: str, results: list) -> None:
    print(f"\n{label}:")
    for result in results:
        print(
            f"  tt_rank={result.tt_rank:>4}  "
            f"size_reduction={result.size_reduction_pct:6.2f}%  "
            f"rel_error={result.relative_reconstruction_error:.4f}"
        )


def main() -> None:
    report = run_phase1a_demo()

    print("=" * 60)
    print("LAIR Compact Models -- Phase 1a pipeline validation (I-19)")
    print("=" * 60)

    _print_results("Constructed low-rank matrix (256x256, true rank 4)", report["low_rank_matrix"])
    _print_results("Incompressible random matrix (256x256)", report["random_matrix"])

    sanity = report["max_rank_sanity_check"]
    print(
        f"\nMax-rank sanity check (tt_rank=256, should be ~exact): "
        f"rel_error={sanity.relative_reconstruction_error:.2e}"
    )

    print(
        "\nSee docs/rfcs/RFC-0003-lair-compact-models.md for what this "
        "does and does not prove -- naive reshape-based tensorization "
        "does not automatically expose a matrix's ordinary low-rank "
        "structure; this is a real, honest Phase 1a finding, not a "
        "negative result to hide."
    )


if __name__ == "__main__":
    main()
