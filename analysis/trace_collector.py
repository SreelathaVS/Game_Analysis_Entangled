import csv
import os
import random
from entangled_engine import (
    EntangledGameSimulation,
    GreedyAgent,
    MinimaxAgent,
    coord_str,
    direction_name,
)


def format_board_matrix_flattened(grid):
  rows_str = ["[" + " ".join(f"{val:2d}" for val in row) + "]" for row in grid]
  return " | ".join(rows_str)


def run_batch_and_collect_traces(
    num_games=1000,
    target_score=3,
    p1_type="random",
    p2_type="random",
    depth=2,
    top_k=4,
    pre_filter_cap=20,
    score_weight=1000,
    mobility_weight=10,
    output_base_dir="outputs",
    force_overwrite=False,
):
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
    #if seed % 100 == 0:
    #  print("running ", seed, "+")

    sim = EntangledGameSimulation(
        p1_type=p1_type, p2_type=p2_type, target_score=target_score
    )

    turn_logs = []
    turn_num = 1

    while True:
      # 1. Start-of-turn check
      game_over, winner, reason = sim.check_game_over(check_stuck=True)
      if game_over:
        batch_results.append({
            "winner": winner,
            "reason": reason,
            "total_moves": sim.move_count,
            "final_scores": sim.scores.copy(),
        })
        if reason not in captured_category_traces:
          captured_category_traces[reason] = (seed, turn_logs)
        break

      current_p = sim.current_player
      active_agent_type = p1_type if current_p == "p1" else p2_type

      coords_dict = (
          sim.board.p1_pieces_coords
          if current_p == "p1"
          else sim.board.p2_pieces_coords
      )

      # 2. Clean, Symmetrical Agent Dispatch Logic
      if active_agent_type == "greedy":
        chosen_pair, move1, move2 = GreedyAgent.select_best_move(sim)

      elif active_agent_type == "minimax":
        chosen_pair, move1, move2 = MinimaxAgent.select_best_move(
            sim,
            depth=depth,
            top_k=top_k,
            pre_filter_cap=pre_filter_cap,
            score_weight=score_weight,
            mobility_weight=mobility_weight,
        )

      else:
        # Uniform Random Agent with Full Candidate Generation
        candidates = MinimaxAgent._generate_full_turn_candidates(
            sim, current_p
        )
        if candidates:
          chosen_pair, move1, move2 = random.choice(candidates)
        else:
          chosen_pair, move1, move2 = None, None, None

      if chosen_pair is None:
        # No moves possible for active player
        break

      pid1, pid2 = chosen_pair[0], chosen_pair[1]
      orig_r1, orig_c1 = coords_dict[pid1]
      orig_r2, orig_c2 = coords_dict[pid2]

      # 3. Execute Turn
      early_end, winner, reason = sim.execute_turn(chosen_pair, move1, move2)

      new_r1, new_c1 = coords_dict[pid1]
      new_r2, new_c2 = coords_dict[pid2]

      dir1 = direction_name(orig_r1, orig_c1, new_r1, new_c1)
      dir2 = direction_name(orig_r2, orig_c2, new_r2, new_c2)

      turn_logs.append({
          "turn": turn_num,
          "player": current_p,
          "agent": active_agent_type,
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
        batch_results.append({
            "winner": winner,
            "reason": reason,
            "total_moves": sim.move_count,
            "final_scores": sim.scores.copy(),
        })
        if reason not in captured_category_traces:
          captured_category_traces[reason] = (seed, turn_logs)
        break

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
      filepath = os.path.join(traces_dir, f"single_game_{cat}.csv")
      if not os.path.exists(filepath) or force_overwrite:
        seed, logs = captured_category_traces[cat]
        with open(filepath, "w", newline="") as f:
          writer = csv.DictWriter(f, fieldnames=fieldnames)
          writer.writeheader()
          for log in logs:
            writer.writerow(log)
        print(f"  [New Trace Created] Saved: {filepath}")
      else:
        print(f"  [Skipped Existing] File already present: {filepath}")

  return batch_results, captured_category_traces