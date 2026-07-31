import csv
import random
from entangled_engine import EntangledGameSimulation

CATEGORIES = [
    "draw_simultaneous_target",
    "p1_win_score",
    "p1_win_opponent_stuck",
    "p2_win_score",
    "p2_win_opponent_stuck",
]


def run_batch(total_games=10000, target_score=5):
  print(
      f"🚀 Running {total_games} batch simulations (Target Score:"
      f" {target_score})...\n"
  )

  category_counts = {cat: 0 for cat in CATEGORIES}

  for game_id in range(1, total_games + 1):
    random.seed(game_id)
    sim = EntangledGameSimulation(
        p1_type="random", p2_type="random", target_score=target_score
    )
    res = sim.run_simulation()

    reason = res["reason"]
    if reason in category_counts:
      category_counts[reason] += 1

    if game_id % 2000 == 0:
      print(f"  Processed {game_id}/{total_games} games...")

  print("\n📊 Batch Results Summary:")
  for cat in CATEGORIES:
    print(f"  - {cat:28s}: {category_counts[cat]} games")

  # Write 5 CSV files with single summary row
  for cat in CATEGORIES:
    filename = f"batch_summary_{cat}.csv"
    with open(filename, "w", newline="") as f:
      writer = csv.writer(f)
      writer.writerow(["category", "game_count", "total_simulations_run"])
      writer.writerow([cat, category_counts[cat], total_games])
    print(f"📂 Saved summary: {filename}")


if __name__ == "__main__":
  run_batch(total_games=10000, target_score=5)