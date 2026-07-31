import csv
import json
import os
import random
from typing import Any, Dict, List, Tuple
from entangled_engine import EntangledGameSimulation, coord_str, direction_name


def format_board_matrix_flattened(grid: List[List[int]]) -> str:
  rows_str = ["[" + " ".join(f"{val:2d}" for val in row) + "]" for row in grid]
  return " | ".join(rows_str)


def run_batch_and_collect_traces(
    num_games: int = 10000,
    target_score: int = 3,
    p1_type: str = "random",
    p2_type: str = "random",
    output_base_dir: str = "outputs",
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:

  # Generate clean nested directory path: outputs/target_score_3/random_vs_random/
  matchup_dir = os.path.join(
      output_base_dir, f"target_score_{target_score}", f"{p1_type}_vs_{p2_type}"
  )
  traces_dir = os.path.join(matchup_dir, "traces")
  os.makedirs(traces_dir, exist_ok=True)

  categories = [
      "draw_simultaneous_target",
      "p1_win_score",
      "p1_win_opponent_stuck",
      "p2_win_score",
      "p2_win_opponent_stuck",
  ]

  batch_results = []
  captured_category_traces = {}

  for seed in range(1, num_games + 1):
    random.seed(seed)
    sim = EntangledGameSimulation(
        p1_type=p1_type, p2_type=p2_type, target_score=target_score
    )

    turn_logs = []
    turn_num = 1

    while True:
      game_over, winner, reason = sim.check_game_over(check_stuck=True)
      if game_over:
        res = {
            "winner": winner,
            "reason": reason,
            "total_moves": sim.move_count,
            "final_scores": sim.scores.copy(),
        }
        batch_results.append(res)
        if reason not in captured_category_traces:
          captured_category_traces[reason] = (seed, turn_logs)
        break

      current_p = sim.current_player
      agent_type = sim.p1_type if current_p == "p1" else sim.p2_type
      coords_dict = (
          sim.board.p1_pieces_coords
          if current_p == "p1"
          else sim.board.p2_pieces_coords
      )

      valid_pairs = sim.board.activePairs(current_p)
      chosen_pair = random.choice(valid_pairs)
      pid1, pid2 = chosen_pair[0], chosen_pair[1]

      orig_r1, orig_c1 = coords_dict[pid1]
      orig_r2, orig_c2 = coords_dict[pid2]

      early_end, winner, reason = sim.execute_turn(chosen_pair)

      new_r1, new_c1 = coords_dict[pid1]
      new_r2, new_c2 = coords_dict[pid2]

      dir1 = direction_name(orig_r1, orig_c1, new_r1, new_c1)
      dir2 = direction_name(orig_r2, orig_c2, new_r2, new_c2)

      turn_logs.append({
          "turn": turn_num,
          "player": current_p,
          "agent": agent_type,
          "moved_pair": str(list(chosen_pair)),
          "p1_move": (
              f"{coord_str(orig_r1, orig_c1)} -> {coord_str(new_r1, new_c1)}"
          ),
          "p1_direction": dir1,
          "p2_move": (
              f"{coord_str(orig_r2, orig_c2)} -> {coord_str(new_r2, new_c2)}"
          ),
          "p2_direction": dir2,
          "p1_score": sim.scores["p1"],
          "p2_score": sim.scores["p2"],
          "board_matrix_flattened": format_board_matrix_flattened(
              sim.board.grid
          ),
      })
      turn_num += 1

      if early_end:
        res = {
            "winner": winner,
            "reason": reason,
            "total_moves": sim.move_count,
            "final_scores": sim.scores.copy(),
        }
        batch_results.append(res)
        if reason not in captured_category_traces:
          captured_category_traces[reason] = (seed, turn_logs)
        break

  # Export Category Traces to CSVs
  fieldnames = [
      "turn",
      "player",
      "agent",
      "moved_pair",
      "p1_move",
      "p1_direction",
      "p2_move",
      "p2_direction",
      "p1_score",
      "p2_score",
      "board_matrix_flattened",
  ]

  for cat in categories:
    if cat in captured_category_traces:
      seed, logs = captured_category_traces[cat]
      filepath = os.path.join(traces_dir, f"single_game_{cat}.csv")
      with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for log in logs:
          writer.writerow(log)

  return batch_results, captured_category_traces