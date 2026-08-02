import copy
import random


class MinimaxAgent:
  """True minimax with alpha-beta pruning and smart move ordering.

  Move ordering ranks each candidate by simulating it once and scoring the
  result -- searching stronger-looking moves first lets alpha-beta prune
  more aggressively. The key implementation detail: each candidate is
  simulated EXACTLY ONCE (that one simulation produces both its ranking
  score and the post-move state used by the search below it). An earlier
  version simulated every candidate once to rank it, then simulated the
  surviving top_k candidates AGAIN inside the search loop -- doubling cost
  everywhere, and since ranking happened before trimming, it paid for the
  ENTIRE unfiltered candidate list at every node of the tree (not just
  top_k), which is what made large batches effectively never finish.

  pre_filter_cap bounds worst-case cost further: if a position has an
  unusually large number of raw candidates, a random subset is taken
  BEFORE the (now single-pass) ranking simulation runs, so cost per node
  stays bounded regardless of how rich branching gets in a given game.
  """

  SCORE_WEIGHT = 1000
  MOBILITY_WEIGHT = 10
  WIN_VALUE = 1_000_000

  @staticmethod
  def select_best_move(
      sim, depth=2, top_k=4, score_weight=1000, mobility_weight=10,
      pre_filter_cap=15,
  ):
    current_p = sim.current_player
    candidates = MinimaxAgent._generate_full_turn_candidates(sim, current_p)
    if not candidates:
      return None, None, None

    # Rank every (pre-filtered) candidate, then trim to top_k -- same
    # bound applied at every level, root included. (An earlier attempt at
    # this fix skipped trimming the root "for thoroughness", which sounds
    # safe but actually multiplies the cost of the next ply by however
    # many candidates survive -- worse than the bug it was fixing.)
    ranked = MinimaxAgent._simulate_and_rank(
        sim, candidates, current_p, score_weight, mobility_weight,
        pre_filter_cap,
    )
    if top_k is not None and len(ranked) > top_k:
      ranked = ranked[:top_k]

    root_player = current_p
    alpha, beta = -float("inf"), float("inf")
    best_value = -float("inf")
    best_candidates = []

    for _heuristic, candidate, sim_copy, game_over, winner in ranked:
      value = MinimaxAgent._minimax_value(
          sim_copy, depth - 1, alpha, beta, root_player, top_k,
          score_weight, mobility_weight, pre_filter_cap, game_over, winner,
      )

      if value > best_value:
        best_value = value
        best_candidates = [candidate]
      elif value == best_value:
        best_candidates.append(candidate)

      alpha = max(alpha, best_value)

    return random.choice(best_candidates)

  @staticmethod
  def _minimax_value(
      sim, depth, alpha, beta, root_player, top_k, score_weight,
      mobility_weight, pre_filter_cap, game_over=None, winner=None,
  ):
    if game_over is None:
      game_over, winner, _ = sim.check_game_over(check_stuck=True)

    if game_over:
      return MinimaxAgent._terminal_value(winner, root_player, depth)

    if depth <= 0:
      return MinimaxAgent._heuristic_value(
          sim, root_player, score_weight, mobility_weight
      )

    current_p = sim.current_player
    candidates = MinimaxAgent._generate_full_turn_candidates(sim, current_p)
    if not candidates:
      return MinimaxAgent._heuristic_value(
          sim, root_player, score_weight, mobility_weight
      )

    # Deeper nodes: rank (single simulation per candidate), THEN trim to
    # top_k -- so cost here is exactly len(pre-filtered candidates)
    # simulations, never 2x, and never the full raw list once capped.
    ranked = MinimaxAgent._simulate_and_rank(
        sim, candidates, current_p, score_weight, mobility_weight,
        pre_filter_cap,
    )
    if top_k is not None and len(ranked) > top_k:
      ranked = ranked[:top_k]

    maximizing = current_p == root_player

    if maximizing:
      value = -float("inf")
      for _h, _candidate, sim_copy, g_over, w in ranked:
        child_value = MinimaxAgent._minimax_value(
            sim_copy, depth - 1, alpha, beta, root_player, top_k,
            score_weight, mobility_weight, pre_filter_cap, g_over, w,
        )
        value = max(value, child_value)
        alpha = max(alpha, value)
        if alpha >= beta:
          break
      return value
    else:
      value = float("inf")
      for _h, _candidate, sim_copy, g_over, w in ranked:
        child_value = MinimaxAgent._minimax_value(
            sim_copy, depth - 1, alpha, beta, root_player, top_k,
            score_weight, mobility_weight, pre_filter_cap, g_over, w,
        )
        value = min(value, child_value)
        beta = min(beta, value)
        if alpha >= beta:
          break
      return value

  @staticmethod
  def _simulate_and_rank(sim, candidates, current_p, score_weight,
                          mobility_weight, pre_filter_cap):
    """Simulates each candidate ONCE and returns
    (heuristic, candidate, sim_copy, game_over, winner) tuples, sorted
    best-first from current_p's own perspective. Callers reuse sim_copy
    for further recursion instead of re-simulating."""
    if pre_filter_cap is not None and len(candidates) > pre_filter_cap:
      candidates = random.sample(candidates, pre_filter_cap)

    ranked = []
    for pair, move1, move2 in candidates:
      sim_copy = copy.deepcopy(sim)
      game_over, winner, _ = sim_copy.execute_turn(pair, move1, move2)
      if game_over:
        heuristic = MinimaxAgent._terminal_value(winner, current_p, 0)
      else:
        heuristic = MinimaxAgent._heuristic_value(
            sim_copy, current_p, score_weight, mobility_weight
        )
      ranked.append((heuristic, (pair, move1, move2), sim_copy, game_over, winner))

    ranked.sort(key=lambda item: item[0], reverse=True)
    return ranked

  @staticmethod
  def _terminal_value(winner, root_player, depth):
    if winner == root_player:
      return MinimaxAgent.WIN_VALUE + depth
    if winner == "draw" or winner is None:
      return 0
    return -MinimaxAgent.WIN_VALUE - depth

  @staticmethod
  def _heuristic_value(sim, root_player, score_weight, mobility_weight):
    opp_player = "p2" if root_player == "p1" else "p1"
    score_diff = sim.scores[root_player] - sim.scores[opp_player]
    my_mobility = len(sim.board.activePairs(root_player))
    opp_mobility = len(sim.board.activePairs(opp_player))
    return score_weight * score_diff + mobility_weight * (
        my_mobility - opp_mobility
    )

  @staticmethod
  def _generate_full_turn_candidates(sim, current_p):
    valid_pairs = sim.board.activePairs(current_p)
    coords_dict = (
        sim.board.p1_pieces_coords
        if current_p == "p1"
        else sim.board.p2_pieces_coords
    )

    candidates = []
    for pair in valid_pairs:
      pid1, pid2 = pair[0], pair[1]
      p1_moves = sim.board.get_valid_moves_for_piece(pid1, pid2, current_p)
      orig_r1, orig_c1 = coords_dict[pid1]

      for mr1, mc1 in p1_moves:
        sim.board.grid[orig_r1][orig_c1] = 0
        sim.board.grid[mr1][mc1] = pid1
        coords_dict[pid1] = (mr1, mc1)

        p2_moves = sim.board.get_valid_moves_for_piece(pid2, None, current_p)

        sim.board.grid[mr1][mc1] = 0
        sim.board.grid[orig_r1][orig_c1] = pid1
        coords_dict[pid1] = (orig_r1, orig_c1)

        for mr2, mc2 in p2_moves:
          candidates.append((pair, (mr1, mc1), (mr2, mc2)))

    return candidates