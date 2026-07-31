from typing import Any, Dict, List
import numpy as np


def compute_simulation_statistics(
    batch_results: List[Dict[str, Any]],
) -> Dict[str, Any]:
  """Computes statistical summary from raw simulation results."""
  total_games = len(batch_results)
  moves = [r["total_moves"] for r in batch_results]

  category_counts = {
      "draw_simultaneous_target": 0,
      "p1_win_score": 0,
      "p1_win_opponent_stuck": 0,
      "p2_win_score": 0,
      "p2_win_opponent_stuck": 0,
  }

  for r in batch_results:
    reason = r["reason"]
    if reason in category_counts:
      category_counts[reason] += 1

  p1_total = (
      category_counts["p1_win_score"] + category_counts["p1_win_opponent_stuck"]
  )
  p2_total = (
      category_counts["p2_win_score"] + category_counts["p2_win_opponent_stuck"]
  )
  draws = category_counts["draw_simultaneous_target"]

  return {
      "total_games": total_games,
      "p1_win_rate": p1_total / total_games,
      "p2_win_rate": p2_total / total_games,
      "draw_rate": draws / total_games,
      "avg_game_length": float(np.mean(moves)),
      "std_game_length": float(np.std(moves)),
      "median_game_length": float(np.median(moves)),
      "min_game_length": int(np.min(moves)),
      "max_game_length": int(np.max(moves)),
      "stuck_game_ratio": (
          category_counts["p1_win_opponent_stuck"]
          + category_counts["p2_win_opponent_stuck"]
      )
      / total_games,
      "score_game_ratio": (
          category_counts["p1_win_score"] + category_counts["p2_win_score"]
      )
      / total_games,
      "category_counts": category_counts,
  }


def compare_experiments(exp1_stats: Dict, exp2_stats: Dict) -> Dict:
  """Helper to compare baseline vs updated or bugged vs fixed runs."""
  return {
      "p1_win_rate_diff": exp2_stats["p1_win_rate"] - exp1_stats["p1_win_rate"],
      "p2_win_rate_diff": exp2_stats["p2_win_rate"] - exp1_stats["p2_win_rate"],
      "avg_length_diff": exp2_stats["avg_game_length"]
      - exp1_stats["avg_game_length"],
      "stuck_ratio_diff": exp2_stats["stuck_game_ratio"]
      - exp1_stats["stuck_game_ratio"],
  }