import csv
import random
from entangled_engine import EntangledGameSimulation, coord_str, direction_name

CATEGORIES = [
    "draw_simultaneous_target",
    "p1_win_score",
    "p1_win_opponent_stuck",
    "p2_win_score",
    "p2_win_opponent_stuck",
]


def format_board_matrix_flattened(grid):
  """Formats a 2D grid matrix into a single-line string separated by pipes."""
  rows_str = []
  for row in grid:
    formatted_row = " ".join(f"{val:2d}" for val in row)
    rows_str.append(f"[{formatted_row}]")
  return " | ".join(rows_str)


def simulate_game_and_record(seed, target_score=5):
  """Plays a full game under seed and records turn-by-turn detailed trace logs."""
  random.seed(seed)
  sim = EntangledGameSimulation(
      p1_type="random", p2_type="random", target_score=target_score
  )

  turn_logs = []
  turn_num = 1

  while True:
    game_over, winner, reason = sim.check_game_over(check_stuck=True)
    if game_over:
      return reason, turn_logs

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

    # Pre-move coordinates
    orig_r1, orig_c1 = coords_dict[pid1]
    orig_r2, orig_c2 = coords_dict[pid2]

    # Execute move inside simulation
    early_end, winner, reason = sim.execute_turn(chosen_pair)

    # Post-move coordinates
    new_r1, new_c1 = coords_dict[pid1]
    new_r2, new_c2 = coords_dict[pid2]

    dir1 = direction_name(orig_r1, orig_c1, new_r1, new_c1)
    dir2 = direction_name(orig_r2, orig_c2, new_r2, new_c2)

    # Capture flattened 2D board state snapshot after turn
    board_state_str = format_board_matrix_flattened(sim.board.grid)

    turn_logs.append({
        "turn": turn_num,
        "player": current_p,
        "agent": agent_type,
        "moved_pair": str(list(chosen_pair)),
        "p1_move": f"{coord_str(orig_r1, orig_c1)} -> {coord_str(new_r1, new_c1)}",
        "p1_direction": dir1,
        "p2_move": f"{coord_str(orig_r2, orig_c2)} -> {coord_str(new_r2, new_c2)}",
        "p2_direction": dir2,
        "p1_score": sim.scores["p1"],
        "p2_score": sim.scores["p2"],
        "board_matrix_flattened": board_state_str,
    })

    turn_num += 1

    if early_end:
      return reason, turn_logs


def find_all_5_category_traces(target_score=5):
  found_categories = {}
  attempts = 0
  seed = 1

  print("🔎 Searching for representative single games across all 5 categories...")

  while len(found_categories) < len(CATEGORIES):
    attempts += 1
    reason, logs = simulate_game_and_record(seed, target_score=target_score)

    if reason in CATEGORIES and reason not in found_categories:
      found_categories[reason] = (seed, logs)
      print(
          f"  ✓ Found category '{reason}' on attempt #{attempts} (Seed: {seed},"
          f" Turns: {len(logs)})"
      )

    seed += 1

  print(
      f"\n🎉 Successfully found all 5 game categories in {attempts} attempts!\n"
  )

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

  for cat in CATEGORIES:
    seed, logs = found_categories[cat]
    filename = f"single_game_{cat}.csv"

    with open(filename, "w", newline="") as f:
      writer = csv.DictWriter(f, fieldnames=fieldnames)
      writer.writeheader()
      for log in logs:
        writer.writerow(log)

    print(f"📂 Saved single-game CSV trace with board states: {filename}")


if __name__ == "__main__":
  find_all_5_category_traces(target_score=3)