import copy
import random


class MinimaxAgent:
  """True minimax with alpha-beta pruning.

  Unlike a design that models the opponent's reply via GreedyAgent, this
  agent recurses on itself: at every ply -- ours or the opponent's -- the
  mover is assumed to pick the move that is best FOR THEM under this same
  search, not a fixed heuristic. That's what makes it minimax rather than
  "our move + their greedy move".

  One ply = one full turn (both pieces of a pair moved). depth counts
  plies to look ahead: depth=2 means "our turn, then their best reply",
  depth=4 adds another full round-trip, etc. Search cost grows roughly
  with (avg branching factor) ** depth, so raise depth cautiously -- use
  top_k to cap branching at each ply if it gets slow.
  """

  # Score differences dominate the heuristic since target_score is low
  # (every point is a large fraction of the win condition); mobility is a
  # light positional tiebreaker on top of that.
  SCORE_WEIGHT = 1000
  MOBILITY_WEIGHT = 1
  WIN_VALUE = 1_000_000

  @staticmethod
  def select_best_move(sim, depth=2, top_k=8):
    current_p = sim.current_player
    candidates = MinimaxAgent._generate_full_turn_candidates(sim, current_p)
    if not candidates:
      return None, None, None

    root_player = current_p
    alpha, beta = -float("inf"), float("inf")
    best_value = -float("inf")
    best_candidates = []

    for candidate in candidates:
      sim_copy = copy.deepcopy(sim)
      pair, move1, move2 = candidate
      game_over, winner, _ = sim_copy.execute_turn(pair, move1, move2)

      value = MinimaxAgent._minimax_value(
          sim_copy, depth - 1, alpha, beta, root_player, top_k,
          game_over, winner,
      )

      if value > best_value:
        best_value = value
        best_candidates = [candidate]
      elif value == best_value:
        best_candidates.append(candidate)

      alpha = max(alpha, best_value)

    return random.choice(best_candidates)

  @staticmethod
  def _minimax_value(sim, depth, alpha, beta, root_player, top_k,
                      game_over=None, winner=None):
    if game_over is None:
      game_over, winner, _ = sim.check_game_over(check_stuck=True)

    if game_over:
      return MinimaxAgent._terminal_value(winner, root_player, depth)

    if depth <= 0:
      return MinimaxAgent._heuristic_value(sim, root_player)

    current_p = sim.current_player
    candidates = MinimaxAgent._generate_full_turn_candidates(sim, current_p)
    if not candidates:
      # Shouldn't happen -- 0 valid pairs is already a game-over "stuck"
      # state caught above -- but fall back safely if it ever does.
      return MinimaxAgent._heuristic_value(sim, root_player)

    if top_k is not None and len(candidates) > top_k:
      candidates = random.sample(candidates, top_k)

    maximizing = current_p == root_player

    if maximizing:
      value = -float("inf")
      for pair, move1, move2 in candidates:
        sim_copy = copy.deepcopy(sim)
        g_over, w, _ = sim_copy.execute_turn(pair, move1, move2)
        child_value = MinimaxAgent._minimax_value(
            sim_copy, depth - 1, alpha, beta, root_player, top_k, g_over, w
        )
        value = max(value, child_value)
        alpha = max(alpha, value)
        if alpha >= beta:
          break
      return value
    else:
      value = float("inf")
      for pair, move1, move2 in candidates:
        sim_copy = copy.deepcopy(sim)
        g_over, w, _ = sim_copy.execute_turn(pair, move1, move2)
        child_value = MinimaxAgent._minimax_value(
            sim_copy, depth - 1, alpha, beta, root_player, top_k, g_over, w
        )
        value = min(value, child_value)
        beta = min(beta, value)
        if alpha >= beta:
          break
      return value

  @staticmethod
  def _terminal_value(winner, root_player, depth):
    if winner == root_player:
      # Reward wins found at a shallower remaining depth (i.e. sooner).
      return MinimaxAgent.WIN_VALUE + depth
    if winner == "draw" or winner is None:
      return 0
    # Opponent won -- penalize losses found sooner more heavily.
    return -MinimaxAgent.WIN_VALUE - depth

  @staticmethod
  def _heuristic_value(sim, root_player):
    opp_player = "p2" if root_player == "p1" else "p1"
    score_diff = sim.scores[root_player] - sim.scores[opp_player]
    my_mobility = len(sim.board.activePairs(root_player))
    opp_mobility = len(sim.board.activePairs(opp_player))
    return (
        MinimaxAgent.SCORE_WEIGHT * score_diff
        + MinimaxAgent.MOBILITY_WEIGHT * (my_mobility - opp_mobility)
    )

  @staticmethod
  def _generate_full_turn_candidates(sim, current_p):
    """Enumerates every legal (pair, move1, move2) full-turn action for
    current_p, using the same in-place-then-revert trick as GreedyAgent so
    no deepcopy is needed just to enumerate options."""
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