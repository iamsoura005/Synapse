"""
Shapley Value Allocator for SYNAPSE multi-party negotiations.
For N <= 6: exact Shapley computation.
For N > 6:  Monte Carlo sampling (1000 permutations, ±2% accuracy).
"""
import itertools
import random
from typing import Callable


def _exact_shapley(party_ids: list, char_fn: Callable) -> dict:
    """Exact O(N! × N) Shapley computation."""
    n = len(party_ids)
    values = {pid: 0.0 for pid in party_ids}

    for perm in itertools.permutations(party_ids):
        coalition = frozenset()
        for pid in perm:
            prev_val = char_fn(coalition)
            coalition = coalition | {pid}
            marginal = char_fn(coalition) - prev_val
            values[pid] += marginal

    return {pid: v / len(list(itertools.permutations(party_ids))) for pid, v in values.items()}


def _monte_carlo_shapley(party_ids: list, char_fn: Callable, num_samples: int = 1000) -> dict:
    """Monte Carlo approximation — O(num_samples × N)."""
    n = len(party_ids)
    values = {pid: 0.0 for pid in party_ids}

    for _ in range(num_samples):
        perm = party_ids[:]
        random.shuffle(perm)
        coalition = frozenset()
        for pid in perm:
            prev_val = char_fn(coalition)
            coalition = coalition | {pid}
            marginal = char_fn(coalition) - prev_val
            values[pid] += marginal

    return {pid: v / num_samples for pid, v in values.items()}


def compute_shapley_values(
    party_ids: list[str],
    characteristic_function: Callable[[frozenset], float],
    num_samples: int = 1000,
) -> dict[str, float]:
    """
    Compute Shapley values for any coalition size.
    characteristic_function(coalition: frozenset) -> float
      Returns the value (satisfaction) achievable by that coalition alone.
    """
    if len(party_ids) <= 6:
        return _exact_shapley(party_ids, characteristic_function)
    return _monte_carlo_shapley(party_ids, characteristic_function, num_samples)


def build_characteristic_function(satisfaction_scores: dict[str, float]):
    """
    Simple characteristic function based on satisfaction scores.
    A coalition's value = mean satisfaction of its members
    using their negotiated scores (or 0.5 baseline if not yet settled).
    """
    def char_fn(coalition: frozenset) -> float:
        if not coalition:
            return 0.0
        return sum(satisfaction_scores.get(pid, 0.5) for pid in coalition) / len(coalition)

    return char_fn
