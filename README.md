# Entangled game analysis

Does looking ahead help a player choose a better turn in Entangled? This Python project simulates games between random, greedy, and minimax players. Each player follows the same rules on a 9-by-7 board. A turn moves two pieces in sequence, so the first move changes which destinations are legal for the second.

## How the players choose

- **Random** picks a legal full turn at random.
- **Greedy** simulates legal turns and chooses the highest immediate net score gain.
- **Minimax** ranks candidate turns and searches a shortlist of opponent replies. It evaluates unfinished positions using score advantage and mobility (the number of available piece pairs). Alpha-beta pruning skips branches that cannot improve the current choice within the searched tree.

## Recorded results

Each row describes a separate 1,000-game batch from the [minimax analysis notebook](minimax_analysis.ipynb). P1 moves first.

| Minimax seat | Opponent | Target score | Minimax wins | Draws |
| --- | --- | ---: | ---: | ---: |
| P1 | Greedy | 5 | 79.4% | 3.1% |
| P1 | Random | 3 | 98.7% | 0.7% |
| P1 | Greedy | 3 | 76.3% | 4.8% |
| P2 | Greedy | 3 | 76.9% | 3.5% |

In the target-three seat comparison, minimax won about 76% of games from either seat. The repository also includes 10,000-game random-versus-random baseline summaries for [target three](outputs/target_score_3/random_vs_random/summary_metrics.json) and [target five](outputs/target_score_5/random_vs_random/summary_metrics.json).

## Explore the project

Start with the saved outputs in the analysis notebook above. To follow a game through the code:

1. [Board setup](entangled_engine/grid_setup.py) defines starting positions, eligible pairs, and legal destinations.
2. [Game simulation](entangled_engine/game_simulation.py) applies a turn, awards points, switches players, and checks for a win or draw.
3. [Greedy](entangled_engine/greedy_agent.py) and [minimax](entangled_engine/minimax_agent.py) implement the two search strategies.
4. The [batch runner](analysis/trace_collector.py) plays the matchups and saves representative turn-by-turn CSV traces. The [optimization notebook](optimize_minimax.ipynb) explores search settings and move time.
