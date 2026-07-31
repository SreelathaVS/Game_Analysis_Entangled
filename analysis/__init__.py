"""Entangled Game Analysis Package

Provides modular routines for batch Monte Carlo simulations, statistical metric
computation, trace collection, and future comparative AI evaluation.
"""

from .metrics import (
    compare_experiments,
    compute_simulation_statistics,
)
from .trace_collector import (
    format_board_matrix_flattened,
    run_batch_and_collect_traces,
)

__all__ = [
    "compute_simulation_statistics",
    "compare_experiments",
    "format_board_matrix_flattened",
    "run_batch_and_collect_traces",
]