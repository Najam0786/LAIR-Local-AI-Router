import numpy as np

from scripts.compactify.pipeline import (
    compress_matrix,
    construct_low_rank_matrix,
    run_phase1a_demo,
)


def test_low_rank_matrix_has_the_requested_ordinary_rank():
    matrix = construct_low_rank_matrix(64, 64, true_rank=3, seed=0)

    assert np.linalg.matrix_rank(matrix) == 3


def test_max_tt_rank_reconstructs_almost_exactly():
    matrix = construct_low_rank_matrix(64, 64, true_rank=4, seed=0)

    result = compress_matrix(matrix, tensorized_shape=(8, 8, 8, 8), tt_rank=64)

    assert result.relative_reconstruction_error < 1e-5


def test_compression_reduces_parameter_count():
    matrix = construct_low_rank_matrix(64, 64, true_rank=4, seed=0)

    result = compress_matrix(matrix, tensorized_shape=(8, 8, 8, 8), tt_rank=2)

    assert result.compressed_params < result.original_params
    assert result.size_reduction_pct > 0.0


def test_demo_runs_and_reports_max_rank_sanity_check():
    report = run_phase1a_demo()

    assert report["max_rank_sanity_check"].relative_reconstruction_error < 1e-5
    assert len(report["low_rank_matrix"]) == len(report["random_matrix"])
