"""
I-19 Phase 1a: a real, reproducible tensor-train / matrix-product-
operator (MPO) compression pipeline, validated mechanically on
synthetic weight-shaped matrices (`tensorly`, numpy-backed -- no
torch, consistent with this project's accessibility mission).

Honest scope (see docs/rfcs/RFC-0003-lair-compact-models.md): this
validates the decomposition/reconstruction math is implemented
correctly and characterizes how compressibility depends on a matrix's
actual rank structure and the chosen tensorization. It does NOT yet
compress a real pretrained model's real weights -- that is Phase 1b,
named future work, blocked on downloading a real model and (per the
plan's own text) the "healing" retrain step needing real GPU time this
pass doesn't have.
"""

from dataclasses import dataclass

import numpy as np
import tensorly as tl
from tensorly.decomposition import tensor_train_matrix


@dataclass
class CompressionResult:
    tt_rank: int
    original_params: int
    compressed_params: int
    size_reduction_pct: float
    relative_reconstruction_error: float


def construct_low_rank_matrix(
    rows: int, cols: int, true_rank: int, seed: int = 0
) -> np.ndarray:
    """
    A synthetic matrix with a known, exact ordinary rank -- a stand-in
    for the kind of learned redundancy real trained weight matrices
    have, used to validate the pipeline against a case with genuine
    low-rank structure (as opposed to incompressible random noise).
    """

    rng = np.random.default_rng(seed)
    a = rng.standard_normal((rows, true_rank)).astype(np.float32)
    b = rng.standard_normal((true_rank, cols)).astype(np.float32)

    return a @ b


def compress_matrix(
    matrix: np.ndarray, tensorized_shape: tuple[int, ...], tt_rank: int
) -> CompressionResult:
    """
    Reshapes `matrix` into `tensorized_shape` (must split evenly into
    input/output factor dims, per `tensorly.decomposition.tensor_train_matrix`'s
    own convention) and compresses it via tensor-train-matrix (MPO)
    decomposition at the given internal rank.
    """

    tensor = matrix.reshape(tensorized_shape)
    factors = tensor_train_matrix(tensor, rank=[1, tt_rank, 1])
    reconstructed = tl.tt_matrix_to_tensor(factors)

    original_params = matrix.size
    compressed_params = sum(factor.size for factor in factors)
    relative_error = float(
        np.linalg.norm(reconstructed - tensor) / np.linalg.norm(tensor)
    )

    return CompressionResult(
        tt_rank=tt_rank,
        original_params=original_params,
        compressed_params=compressed_params,
        size_reduction_pct=100.0 * (1 - compressed_params / original_params),
        relative_reconstruction_error=relative_error,
    )


def run_phase1a_demo() -> dict:
    """
    Reproduces the Phase 1a finding: a matrix with real (constructed)
    low-rank structure compresses far better, at the same TT-rank
    budget, than an incompressible random matrix of identical shape --
    but only when the chosen tensorization actually exposes that
    structure. Returns a plain dict so `scripts/compactify/run_demo.py`
    (and tests) can both consume it without re-running the numerics.
    """

    tensorized_shape = (16, 16, 16, 16)
    ranks = [1, 2, 4, 8, 16]

    low_rank_matrix = construct_low_rank_matrix(256, 256, true_rank=4, seed=0)
    random_matrix = np.random.default_rng(1).standard_normal((256, 256)).astype(
        np.float32
    )

    return {
        "low_rank_matrix": [
            compress_matrix(low_rank_matrix, tensorized_shape, r) for r in ranks
        ],
        "random_matrix": [
            compress_matrix(random_matrix, tensorized_shape, r) for r in ranks
        ],
        "max_rank_sanity_check": compress_matrix(
            low_rank_matrix, tensorized_shape, tt_rank=256
        ),
    }
